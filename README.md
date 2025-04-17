# vivino-scanner

This app scans wine pdfs (htmls will be another challenge) and extracts as much info as possible from them. It uses Google's Gemini Flash 2.0 to do this. Eventually, I will fine tune my own model to do this, but this is a start. Then, it uses [Vivino](https://www.vivino.com/) to find the wine and get as much info from there as possible. Unfortunately, the Vivino API is rough and does not allow for search so I am scraping the site.

*Current Functionality:*
- Scan pdfs and extract text using Google's Gemini Flash 2.0.
- Use the extracted text to find the wine on Vivino and get as much info as possible.
- Plots Data and let's you explore the wine menu

*PLAN:*
- Build in better graphs and data exploration
- Add more guardrails to the code as their remains a lot of room for error
- Use a local model that is fine tuned for this task
   * Try a image based agentic model as wine menus are often extremely varied in formatting; text scanning can be rough
   * Modify text pulldowns to be more robust

*Questions*
If you have any questions or suggestions, please feel free to reach out to me at [@austinbarish](https://linkedin.com/in/austinbarish/) on LinkedIn or email me at barishaustin@gmail.com.