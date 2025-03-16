import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-S", '--Server')

args = parser.parse_args()

raw  = r'{0}'.format(args.Server)
with open(raw,'r') as f:
    data = f.read()
    print(data)
