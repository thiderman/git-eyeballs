import sys
import os
import subprocess as sp
import argparse
import yaml

import dateutil.parser
from blessings import Terminal
from operator import attrgetter

TERM = Terminal()


class Runner(object):
    def __init__(self):
        self.reviews = []
        self.config = {}

    def setup(self):
        self.gitroot = self.get_git_root()

        with open('.codereview.yaml') as f:
            self.__dict__.update(yaml.load(f))

    def list(self):
        for x, review in enumerate(self.reviews, start=1):
            review.print_short(x)

    def get_git_root(self):
        if os.path.isdir('.git'):
            return os.getcwd()

        proc = sp.Popen(
            ['git', 'rev-parse', '--git-dir'],
            stdout=sp.PIPE,
            stderr=sp.PIPE,
        )
        stdout, stderr = [x.decode() for x in proc.communicate()]

        if stderr:
            print(stderr)
            sys.exit(128)

        if stdout == '.git\n':
            return os.getcwd()
        return stdout

    def load_reviews(self):
        files = self.git('ls-tree', '-r', self.branch, '--name-only')

        for f in files.strip().split('\n'):
            content = self.git('show', '{0}:{1}'.format(self.branch, f))
            review = Review.load(content)
            self.reviews.append(review)

        self.reviews = sorted(self.reviews, key=attrgetter('merged'))

    def git(self, *args):
        # print('git: {0}'.format(' '.join(args)))
        proc = sp.Popen(
            ['git'] + list(args),
            stdout=sp.PIPE,
            stderr=sp.PIPE,
        )
        stdout, stderr = [x.decode() for x in proc.communicate()]
        return stdout


class Review(object):
    def __init__(self, data):
        self.data = data
        self.created = None

    def setup(self):
        self.created = dateutil.parser.parse(self.data['dates']['created'])
        self.merged = self.data['merged']

    def new(self, branch, target):
        pass

    @staticmethod
    def load(content):
        review = Review(yaml.load(content))
        review.setup()
        return review

    def merge(self):
        pass

    def print_short(self, index):
        data = [
            TERM.bold_black('{0}) '.format(index)),
            TERM.bold_yellow(self.data['title']),
        ]

        data.append(
            TERM.bright_black(' (') +
            TERM.bold_blue(self.data['from']['branch']) +
            TERM.bright_black(':') +
            TERM.bold_cyan(self.data['onto'])
        )

        if self.merged:
            data.append(
                TERM.bright_black(', ') +
                TERM.bold_green('MERGED')
            )

        data.append(TERM.bright_black(')'))

        print(''.join(data))


def setup_arguments():
    parser = argparse.ArgumentParser('codereview')
    subparsers = parser.add_subparsers(help="Core commands", dest="command")

    subparsers.add_parser(
        'new',
        help="Create a new review"
    )
    subparsers.add_parser(
        'list',
        help="List reviews"
    )
    return parser


def main():
    args = setup_arguments()
    ns = args.parse_args()

    runner = Runner()
    runner.setup()

    if not ns.command or ns.command == 'list':
        runner.load_reviews()
        runner.list()

    if ns.command == 'new':
        print('Creating new review')


if __name__ == "__main__":
    main()