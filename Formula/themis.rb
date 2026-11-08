class Themis < Formula
  desc "CLI and terminal UI for the Themis programming judge"
  homepage "https://github.com/danielgrbacbravo/themis"
  url "https://github.com/danielgrbacbravo/themis/releases/download/v0.1.0/themis_0.1.0_source.tar.gz"
  version "0.1.0"
  sha256 "878c6ec9450344904d41678a0276f537a06f081d37bc9c6d546cfb37eeb224fb"
  license "GPL-3.0-only"

  depends_on "go" => :build
  depends_on "poppler"

  def install
    ENV["CGO_ENABLED"] = "0"
    ENV["GOFLAGS"] = "-mod=vendor"
    system "go", "build", *std_go_args(ldflags: "-s -w -X main.version=#{version}"), "./cmd/themis"
    doc.install "docs/agent-cli.md"
  end

  test do
    assert_match "themis #{version}", shell_output("#{bin}/themis --version")
    output = JSON.parse(shell_output("#{bin}/themis capabilities --json"))
    assert_equal "ok", output.fetch("status")
    assert_includes output.fetch("data").fetch("commands"), "setup plan"
  end
end
