"""
Command line entry point for WalkMyGraph
"""

import sys
from argparse import ArgumentParser

from ngwidgets.cmd import WebserverCmd

from wmg.walk import WalkSet
from wmg.webserver import WmgWebserver


class WalkMyGraphCmd(WebserverCmd):
    """
    Command Line Interface for WalkMyGraph
    """

    def getArgParser(self, description: str, version_msg) -> ArgumentParser:
        """
        get the argument parser
        """
        parser = super().getArgParser(description, version_msg)
        parser.add_argument(
            "--tell",
            metavar="WALKFILE",
            help="tell the stories of the walks of the given walk file",
        )
        parser.add_argument(
            "--validate",
            metavar="WALKFILE",
            help="validate the given walk file as told walks",
        )
        return parser

    def handle_args(self, args) -> bool:
        """
        handle the command line arguments
        """
        handled = False
        if args.tell:
            walk_set = WalkSet.of_yaml(args.tell)
            for walk_key in walk_set.walks:
                print(walk_set.tell(walk_key))
            handled = True
        if args.validate:
            walk_set = WalkSet.of_yaml(args.validate)
            findings = walk_set.validate(told=True)
            for finding in findings:
                print(finding)
            print(f"{len(findings)} findings")
            handled = True
        if not handled:
            handled = super().handle_args(args)
        return handled


def main(argv: list = None):
    """
    Main entry point for WalkMyGraph CLI.
    """
    cmd = WalkMyGraphCmd(
        config=WmgWebserver.get_config(),
        webserver_cls=WmgWebserver,
    )
    exit_code = cmd.cmd_main(argv)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
