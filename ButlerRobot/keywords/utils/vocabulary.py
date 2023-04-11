import os

# File to get vocabulary
def get_vocabulary():
    file_dir = os.path.dirname(os.path.realpath(__file__))
    vocab_path = f'{file_dir}/vocabulary.tsv'
    with open(vocab_path, 'r') as f:
        seed_words = [line.split('\t')[0] for line in f]
    if len(seed_words) <= 0:
        raise Exception(f'The length of seed words should be larger than zero. Loaded from {vocab_path}')
    return seed_words