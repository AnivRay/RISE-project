# RISE-project
07/01/19
- First day at the lab
- Learned Python using Python tutorials

07/02/19 -> 07/05/19
- Used ast parser to create node trees from Python files
- Made a web scraper to access the Kodi website and download add-ons
  - Downloaded the 36 most popular add-ons
  
07/08/19 -> 07/12/19
- Downloaded the next 108 most popular Kodi add-ons using the web scraper
- Created sets of methods that are used to connect to the internet and the libraries they come from
- Tried to identify urls in kodi add-on code using the ast trees
- Problem: The ast analysis fails if the url is stored in a variable or comes as a parameter to a method
- Researched ways to implement a control flow graph and chose the pyt github repository
- Tested pyt code and used it to create a cfg (for default Yahoo)
  
07/15/19 -> 07/18/19
- Used pyt module to create a cfg analysis in order to find the url
- Ran cfg analysis on downloaded Kodi add-ons
- Errors
  - Maximum recursion limit reached
  - Conversion from Python 2 to 3 failed

07/19/19
- Ran the cfg analysis on 108 more add-ons and detected 5 uses of http
- Expanded definitions of connection methods and connection classes to more accurately identify connection methods
- Identified the vulnerability in the OpenSubtitles add-on and why the cfg is not detecting it
- Problem: The CFG maker can not find function calls that are not directly called in the file

07/22/19
- Created visualization of cfg using the graphviz add-on
- Added detection of user input to the graph analysis
  - Can detect user input in the OpenSubtitles add-on

07/23/19
- Validated that detected urls are real urls
- Found connection between user input and connection methods by tracing back the cfg
- Started implementing the taint analysis to find vulnerabilities

07/24/19
- Examined the Taint Analysis propagation method
- Altered Source/Sink definitions to detect user input as a source and connection methods/file executions as sinks

07/25/19
- Sucessfully tracked user input to connection methods
- Found out how the Taint analysis worked

07/26/19
- Changed cfg code to convert "with as" statements to "assignment" statements
- Identified issue in Opensubtile add-on using cfg
- Problem: the issue in Opensubtiles is still not correctly determined to be a vulnerability


