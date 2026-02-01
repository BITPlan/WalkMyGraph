"""
Command line entry point for WalkMyGraph
"""

from argparse import ArgumentParser, Namespace

from basemkit.base_cmd import BaseCmd
from wmg.version import Version


class WalkMyGraphCmd(BaseCmd):
    """Command Line Interface for WalkMyGraph"""

    def getArgParser(self, description: str, version_msg) -> ArgumentParser:
        parser = super().getArgParser(description, version_msg)
        # NO additional arguments for now
        return parser

    def handle_args(self, args: Namespace) -> bool:
        handled = super().handle_args(args)
        if handled:
            return True

        # No additional commands for 0.0.2
        # Just show help if no args
        if not any(vars(args).values()):
            self.parser.print_help()
            return True

        return False


def main(argv=None):
    """Main entry point for WalkMyGraph CLI."""
    exit_code = WalkMyGraphCmd.main(Version(), argv)
    return exit_code


if __name__ == "__main__":
    main()
