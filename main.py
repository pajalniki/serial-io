import argparse
from app import run

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--production', action='store_true', help='Омтетьте, если запускаете в боевом режиме')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = get_args()
    run(args)
