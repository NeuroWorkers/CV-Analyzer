import re

ENGLISH_INTERJECTIONS_AND_CONJUNCTIONS = [
    "wow",  # expression of surprise
    "like",  # filler word
    "so",  # conjunction
    "well",  # filler word
    "you know",  # filler phrase
    "okay",  # agreement
    "hey",  # greeting
    "yeah",  # agreement
    "yes",  # agreement
    "and",  # conjunction
    "or",  # conjunction
    "but",  # conjunction
    "because",  # conjunction
    "if",  # conjunction
    "when",  # conjunction
    "while",  # conjunction
    "then",  # conjunction
    "although",  # conjunction
    "that",  # conjunction
    "how",  # conjunction
    "as",  # conjunction
    "yet",  # conjunction
    "still",  # conjunction
    "only",  # conjunction
    "all",  # conjunction
    "just",  # conjunction
    "time",  # conjunction
    "whether",  # conjunction
    "indeed",  # conjunction
    "really",  # conjunction
    "already",  # conjunction
    "so",  # conjunction
    "thus",  # conjunction
    "also",  # conjunction
    "too",  # conjunction
    "instead",  # conjunction
    "even though",  # conjunction
    "in order to",  # conjunction
    "so that",  # conjunction
]

# List of Russian interjections and conjunctions
# This list is not exhaustive and may need to be expanded
# depending on the specific use case.

RUSSIAN_INTERJECTIONS_AND_CONJUNCTIONS = [
    "ну",  # well, so
    "вот",  # here is, here's
    "типа",  # like, sort of
    "блин",  # darn, shoot (mild curse)
    "окей",  # okay
    "ладно",  # alright, fine
    "ей",  # hey
    "ага",  # uh-huh, yeah
    "да",  # yes
    "и",  # and
    "или",  # or
    "но",  # but
    "а",  # but, and (depending on context)
    "потому что",  # because
    "чтобы",  # in order to, so that
    "если",  # if
    "когда",  # when
    "пока",  # while, until
    "так",  # so, thus
    "тоже",  # also, too
    "то",  # then
    "же",  # indeed, really
    "ли",  # whether
    "как",  # how, as
    "зато",  # but instead, yet
    "хотя",  # although, even though
    "что",  # that
    "уже",  # already
    "еще",  # still, yet
    "только",  # only
    "все",  # all
    "всего",  # only, just
    "тогда",  # then
    "потому",  # because
    "раз",  # time, if
    "если",  # if
    "чтобы",  # so that
    "хотя",  # although
    "пока",  # while
    "когда",  # when
    "тогда",  # then
    "потому",  # because
    "то",  # then
    "ли",  # whether
    "как",  # how
    "зато",  # but instead
    "хотя",  # although
    "тоже",  # also
    "же",  # indeed
    "уже",  # already
    "еще",  # still
    "только",  # only
    "все",  # all
    "всего",  # only
    "раз",  # time
]


def remove_interjections_singlewords(strings):
    pass

def remove_interjections(strings):
    """
    Removes common interjections from a list of strings.

    Args:
        strings: A list of strings.

    Returns:
        A new list of strings with interjections removed.
    """

    inter=RUSSIAN_INTERJECTIONS_AND_CONJUNCTIONS + ENGLISH_INTERJECTIONS_AND_CONJUNCTIONS
    s2=[]
    for string in strings:
        arr = string.split()
        for s in arr:
            s_t=re.sub(r'[,.]', '', s)
            if not s_t in inter:
                s2.append(s)
            else:
               print("found=" + s)
        
        #cleaned_strings.append(cleaned_string)

    return s2 # cleaned_strings
