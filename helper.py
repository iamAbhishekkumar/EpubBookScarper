import re

def remove_tags(string: str):
    return re.sub('<(.*?)>+', "", string)