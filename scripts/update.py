#!/usr/bin/env python3
"""Pin the formula to the latest stable, checksum-verified public release."""
import hashlib
import json
import pathlib
import re
import subprocess
import tempfile

REPO = "danielgrbacbravo/themis"
ROOT = pathlib.Path(__file__).resolve().parents[1]


def fetch(url):
    if url == f"https://api.github.com/repos/{REPO}/releases/latest":
        return subprocess.run(["gh", "api", f"repos/{REPO}/releases/latest"], check=True, capture_output=True, timeout=90).stdout
    prefix = f"https://github.com/{REPO}/releases/download/"
    if not url.startswith(prefix):
        raise ValueError("Unexpected download origin")
    tag, name = url[len(prefix):].split("/")
    with tempfile.TemporaryDirectory() as directory:
        path = pathlib.Path(directory) / "asset"
        subprocess.run(["gh", "release", "download", tag, "--repo", REPO, "--pattern", name, "--output", str(path)], check=True, capture_output=True, timeout=90)
        return path.read_bytes()


def main():
    try:
        release = json.loads(fetch(f"https://api.github.com/repos/{REPO}/releases/latest"))
    except subprocess.CalledProcessError as error:
        if b"HTTP 404" in error.stderr:
            print("No public stable release yet; leaving the formula unchanged.")
            return
        raise
    tag = release["tag_name"]
    if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", tag) or release["draft"] or release["prerelease"]:
        raise ValueError("Expected a published stable semantic version")
    version = tag[1:]
    path = ROOT / "Formula/themis.rb"
    if path.exists():
        current = re.search(r'^  version "([0-9.]+)"$', path.read_text(), re.M)
        if current and tuple(map(int, current[1].split('.'))) >= tuple(map(int, version.split('.'))):
            print("Formula already up to date.")
            return
    name = f"themis_{version}_source.tar.gz"
    prefix = f"https://github.com/{REPO}/releases/download/{tag}/"
    sums = fetch(prefix + "SHA256SUMS").decode()
    expected = None
    for line in sums.splitlines():
        fields = line.split()
        if len(fields) == 2 and fields[1].lstrip('*') == name:
            expected = fields[0]
    if expected is None or not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("Source checksum missing from release")
    archive = fetch(prefix + name)
    if hashlib.sha256(archive).hexdigest() != expected:
        raise ValueError("Source archive checksum mismatch")
    formula = r'''class Themis < Formula
  desc "CLI and terminal UI for the Themis programming judge"
  homepage "https://github.com/danielgrbacbravo/themis"
  url "SOURCE_URL"
  version "VERSION"
  sha256 "CHECKSUM"
  license "GPL-3.0-only"

  depends_on "go" => :build
  depends_on "poppler"

  def install
    ENV["CGO_ENABLED"] = "0"
    ENV["GOFLAGS"] = "-mod=vendor"
    system "go", "build", *std_go_args(ldflags: "-s -w -X main.version=#{version}"), "./cmd/themis"
    doc.install "docs/agent-cli.md"
    Dir.glob("vendor/**/*").each do |path|
      next unless File.file?(path) && File.basename(path).match?(/\A(?:LICENSE|NOTICE|COPYING|COPYRIGHT|AUTHORS)/i)

      relative = Pathname(path).relative_path_from(Pathname("vendor"))
      (pkgshare/"licenses"/relative.dirname).install path
    end
  end

  test do
    assert_predicate pkgshare/"licenses", :directory?
    assert_match "themis #{version}", shell_output("#{bin}/themis --version")
    output = JSON.parse(shell_output("#{bin}/themis capabilities --json"))
    assert_equal "ok", output.fetch("status")
    assert_includes output.fetch("data").fetch("commands"), "setup plan"
  end
end
'''
    formula = formula.replace("SOURCE_URL", prefix + name).replace("VERSION", version).replace("CHECKSUM", expected)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(formula)
    print(f"Updated formula to {tag}")


if __name__ == "__main__":
    main()
