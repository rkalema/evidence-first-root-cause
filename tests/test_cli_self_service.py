from __future__ import annotations

from efrc import build_parser


def test_cli_exposes_self_service_commands():
    parser = build_parser()
    for command in ("init", "doctor", "demo", "investigate"):
        args = parser.parse_args([command])
        assert args.command == command


def test_investigate_accepts_repeated_sources():
    args = build_parser().parse_args(
        [
            "investigate",
            "--question",
            "Why did SLA fall?",
            "--source",
            "a.csv",
            "--source",
            "b.csv",
            "--domain",
            "operations",
        ]
    )
    assert len(args.source) == 2
    assert args.domain == "operations"
