import re


class PragmaParser:
    @staticmethod
    def parse_pragma(file_content: str) -> list:
        """
        Parses the content of a Solidity file to extract all pragma solidity version directives.

        :param file_content: The content of the Solidity file as a string.
        :return: A list of parsed version conditions with operators from all pragma directives in the file.
        """
        pragma_regex = re.compile(r'pragma\s+solidity\s+(.+);')
        matches = pragma_regex.findall(file_content)

        if not matches:
            return []

        parsed_conditions = []
        for version_string in matches:
            # Split by logical operators (|| and &&)
            conditions = re.split(r'\|\||&&', version_string.strip())

            for condition in conditions:
                condition = condition.strip()
                version_match = re.match(r'([><^~]?=?)\s*(\d+(\.\d+){0,2})', condition)
                if version_match:
                    operator = version_match.group(1)
                    version = version_match.group(2)
                    parsed_conditions.append({'operator': operator, 'version': version})
                else:
                    parsed_conditions.append({'error': f'Failed to parse: {condition}'})

        return parsed_conditions
