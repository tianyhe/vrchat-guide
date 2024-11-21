from spellchecker import SpellChecker


def auto_correct(sentence):
    spell = SpellChecker()

    # Detect potentially misspelled words
    misspelled = spell.unknown(sentence.split())

    corrected_words = []
    for word in sentence.split():
        if word in misspelled:
            # Replace the word with its correction
            corrected_words.append(spell.correction(word))
        else:
            # Keep the original word
            corrected_words.append(word)

    # Join the words to form the corrected sentence
    corrected_sentence = ' '.join(corrected_words)

    return corrected_sentence

