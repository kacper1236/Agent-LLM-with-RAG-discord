from langchain_community.document_loaders import PlaywrightURLLoader #AFTER DOWNLOAD WRITE COMMAND: PLAYWRIGHT INSTALL
import re;

urls = ["https://discord.com/guidelines"]

loader = PlaywrightURLLoader(urls=urls, headless=True, remove_selectors=['.link-terms', '.link-terms > *', '.menu-numbers', '[data-animation="over-right"]', 'div.dropdown-language-name', '#onetrust-policy-text > *', '#onetrust-consent-sdk > *', '#locale-dropdown > *', '#locale-dropdown', '.locale-container', 'iframe', 'script', '* > .language', 'div.language', '.language > *', '.archived-link', '.footer-black > *', '.link-terms', '#localize-widget', '#localize-widget > *'])

data = loader.load()

d = data[0].page_content.split('\n\n')
expPoint = r"\d+\. "
expNawias = r"(.*)(\([^\)]+\))$"

points = []
started = False
for line in d:
    du = re.match(expPoint, line)
    if line[0] == 'б': break
    if line == 'Follow the Law': continue
    if line == 'Respect Discord': continue
    if line == 'Respect Each Other': continue
    if line.startswith('For more information '): continue
    if du is not None:
        if (started == True):
            ma = re.match(expNawias, points[len(points)-1], re.MULTILINE)
            if ma is not None:
                points[len(points)-1] = points[len(points)-1].replace(ma.group(2), '')
            points[len(points)-1] = points[len(points)-1].strip()

            # if points[len(points) - 1].endswith(')\n'): continue

        started = True
        points.append(line + '\n')
    else:
        if started == True:
            if (line.startswith("If you see any")):
                ma = re.match(expNawias, points[len(points) - 1], re.MULTILINE)
                print('ma', expNawias, ma)
                if ma is not None:
                    points[len(points) - 1] = points[len(points) - 1].replace(ma.group(2), '')
                points[len(points) - 1] = points[len(points) - 1].strip()

                break
            points[len(points)-1] = points[len(points)-1].strip() + line + '\n'
i = 0
for point in points:
    points[i] = point.strip();
    i = i +1

content = '\n'.join(point for point in points)