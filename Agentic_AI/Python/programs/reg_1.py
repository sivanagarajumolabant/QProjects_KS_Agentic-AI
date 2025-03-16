import re

pattern = r'\d+ \d+'
text = "There are 42 30 apples."
match = re.search(pattern, text)
print(match)
print(match.group())


text = "Hello, world!"
str = 'naga sivaji siva'
print(re.match(r'Hello', text))
print(re.search(r'world', text))
print(re.match(r'world', text))
print(re.match('siva', str))
print(re.search('sivaji', str).group())


text = "The rain in Spain staysin mainly in the plain."
# pattern = r'in'
# pattern = r'\bin\b'
pattern = r'\s+in\s+'
# pattern = r'\s*in\s*'
matches = re.findall(pattern, text)
print(matches)


# text = "The rain in Spain."
text = "The rainSpain in Spain "
new_text = re.sub(r'\s*Spain\s*', 'France', text)
print(new_text)  # Output: The rain in France.

# \sword\s -> it will check whitespace before & aftre the keyword
# \s+word\s+ -> it is same as \s
# \s*word\s* -> it will check anywhere


import re



email_data = 'Contact us siva.m_504504@gmail.com siva.n@quadranttechnologies.com'
all_emails =  re.findall(r'[a-zA-Z0-9._%]+@[a-zA-Z0-9]+\.[a-zA-Z0-9]+', email_data)
print(all_emails)

text = "cat bat mat"
matches = re.findall(r'[bcm]at', text)
print(matches)  # Output: ['bat', 'cat', 'mat']

# text = "Contact us at 123-456-7890 or 987-654-3210."
# text = "Contact us at 1234567890 or 9876543210."
text = "Contact us at 123-456-7890 or 987-654-3210."

# get_ph = re.findall(r'[0-9-]+',text)
get_ph = re.findall(r'\d{3}-\d{3}-\d{4}',text)
print(get_ph)


import re

# text = "Apples are amazing and bananas are beautiful."
text = "Apples are amazing 90 and bananas are beautiful."
# pattern = r'[aA]\w*'  # Words starting with 'A' or 'a'
pattern = r'[a-zA-Z]+\s*\d+\s*\w*'  # Words starting with 'A' or 'a'

matches = re.findall(pattern, text)
print(matches)  # Output: ['Apples', 'are', 'amazing']


text = "The meeting is scheduled for 2023-09-20 and the report is due on 2023/09/25."
# pattern = r'\d{4}[-/]\d{2}[-/]\d{2}'  # Matches dates in YYYY-MM-DD or YYYY/MM/DD format
pattern = r'\d{4}[-/]\d{2}[-/]\d{2}'  # Matches dates in YYYY-MM-DD or YYYY/MM/DD format

dates = re.findall(pattern, text)
print(dates)  # Output: ['2023-09-20', '2023/09/25']