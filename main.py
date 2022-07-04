#
#	Author: Théo Huaumé
#	Project: Compare_JSON_with_PATTERNS
#
#	Purpose: Compare a JSON file with a list of patterns
#

import json
from os import listdir
from os.path import isfile, join

source_file = 'sample_to_study.json'
pattern_dir = 'patterns/'
output_file = 'comparison_summary.txt'


# ---

def get_values_from_json(json, source, pattern_path):
    """
    Recursively retrieve the JSON values verified by the pattern

    :param dict json:
    :param list source:
    :param string pattern_path:
    :return:
    """

    # Stopping condition
    if len(source) == 0:
        return json

    first_value = source[0]

    is_int = False
    if first_value.isdigit():
        first_value = int(first_value) - 1
        is_int = True

    # Wildcard
    if first_value == '*':
        values_list = list()
        for i in range(len(json)):
            values_list.append(get_values_from_json(json[i], source[1:], pattern_path))
        return values_list

    missing = False
    # Index out of range
    if is_int:
        if first_value > len(json):
            missing = True
    # Missing branch case
    else:
        if not first_value in json:
            missing = True

    if missing:
        print("The following element was not found in the json: ", ".".join(source) + " ({0})".format(pattern_path))
        return "???"

    # Nominal case
    return get_values_from_json(json[first_value], source[1:], pattern_path)


# ---

class Error:

    def __init__(self, pattern, suberrors):
        self.error_message = pattern["error"]
        self.recommandation = pattern["recommandation"]
        self.additional_information = " ; ".join(suberrors)
        self.critical = pattern["critical"]

    def __str__(self):
        return """_______________________

Error: {error_message}
Recommandation: {recommandation}
Additional informations: {suberrors}
Critical: {critical}""".format(error_message=self.error_message, recommandation=self.recommandation,
                               suberrors=self.additional_information, critical=self.critical)


# ---

if __name__ == '__main__':
    # TODO/ Missing support for:
    # - int comparisons
    # - boolean operators
    # - expecting everything but <>

    errors = list()

    # ---

    with open(source_file, 'r') as results_file:
        oftester_results = json.load(results_file)

    # ---

    temp_pattern_files = [f for f in listdir(pattern_dir) if isfile(join(pattern_dir, f))]
    temp_pattern_files.sort()

    pattern_files = list()
    for temp_pattern_path in temp_pattern_files:

        # If the file name begins with either a hash or a capital letter, it is ignored
        if temp_pattern_path[0] not in '#ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            pattern_files.append(temp_pattern_path)

    for pattern_path in pattern_files:

        try:
            with open(pattern_dir + pattern_path, 'r') as pattern_file:
                pattern = json.load(pattern_file)
        except json.decoder.JSONDecodeError as err:
            print(err)

        matching_subpatterns = list()

        for subpattern in pattern["subpatterns"]:

            conditions_number = len(subpattern["checks"])
            matching_conditions = list()

            for condition in subpattern["checks"]:

                source = condition["source"].split('.')
                expected = condition["expected"]

                matching_conditions.append(False)

                values = get_values_from_json(oftester_results, source, pattern_path)
                if isinstance(values, str) or isinstance(values, int) or isinstance(values, float):
                    values = [values]

                for v in values:
                    if v == expected:
                        matching_conditions[-1] = True

            # If all conditions ("checks") are met
            if not False in matching_conditions:
                matching_subpatterns.append(subpattern["meaning"])

        if len(matching_subpatterns) != 0:
            errors.append(Error(pattern, matching_subpatterns))

            # Critical: there is no need to go further
            if pattern["critical"]:
                break

    # ---

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Loaded patterns: {0}".format(pattern_files))
        print("Loaded patterns:", pattern_files)

        for err in errors:
            f.write('\n' + str(err))
            print(str(err))

        f.write("\n_______________________\n\nDone")
        print("_______________________\n\nDone")
