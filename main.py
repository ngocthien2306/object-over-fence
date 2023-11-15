from module_fence.inference import main as fence
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description='Description of your script')
    # Add any command-line arguments you need
    parser.add_argument('--module', default='fence', type=str, help='Description of argument 1')
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = parse_arguments()
    if args.module == 'fence':
        fence()