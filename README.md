# Deutsche Telekom Press Releases RAG

-add image here-

## Components
  - a data store (Vector DB)
  - a data ingestion / indexing service (using embeddings from the [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) open-source model)
  - a retrieval service / component for finding matching documents
  - a connection to OpenAI's public LLM service, which it prompts for a good answer to the user's question using relevant context
  - a streamlit interactive component that we can ask questions about announcements and publications of Deutsche Telekom


## The data
  - 250 press releases of Deutsche Telekom
  - The data was scraped from Deutsche Telekom's [press releases website](https://www.telekom.com/en/media/media-information) and cleaned from any HTML/CSS/Script markup
  - The language of all texts is English
  - Some light parsing was applied to get better results


## Flow
### Main app
1. Run this command: `docker-compose up --build -d`. This will do 3 things, in order:
    - Start the PostgreSQL client
    - Create the databse if it doesn't exist
    - Start the streamlit app. It can be accessed locally: http://localhost:8501/

2. From this point forward the user can use the streamlit app. But since we didn't scrape any data and we didn't add any data to the DB the user will not get any answer

### Scraping & Data Ingestion
1. Provided that you ran the above command you can now run both the scraper and the data ingestion from within the docker container of the main app which was already created. Go inside the container with `docker exec -it rag_app /bin/bash`
2. Run the scraper with `python -m scraping.scraping`. The `JSON` files with the press release contents will be saved to `/app/press_releases/`. Also, the files will be mapped to the local `./press_releases/` directory from the project's root
3. Run the ingestion with `python -m database.ingest`. The press release chunks will be embedded and saved to the vector DB
4. Now if the user asks a (relevant) question in the web app, they should get a response
5. You can stop the application with: `docker-compose down --volumes`


## Development

### 1. Scraping
  - Deutsche Telekom's press releases can be accessed on their [media information webpage](https://www.telekom.com/en/media/media-information).
    Loading more press releases from this page we can see that the press releases are returned to network requests of this format:
    
    ```
    https://www.telekom.com/dynamic/fragment/com16/en/418728
    GET params = {
        viewtype = "asFeedList",
        dateFrom_string = ""
        dateFrom = ""
        dateTo_string = ""
        dateTo = ""
        page_active = "1"
        page_next = "2"
        _ = "1754906956075"
    }
    ```
    Leveraging the `page_active` parameter we can programmatically retrieve article URLs until we get to the desired number of press releases.

  - Once we have the list of press release URLs we can run python's `requests.get` method on the URLs to get the HTML 
    content of the press releases and using `BeautifulSoup` we can parse that content

  - We are interested in the text content of the press release, any table data, and all relevant metadata 
    of the content (article author, title, published date, etc.). Everything else can be discarded (images, generic headers, footers, etc.)

  - In order to use this information and save it to the vector DB we need to split it into chunks. These chunks will 
    then be matched against the user's question for similarity

  - So a natural question arises: **How do we split the press releases?**
    The splitting algorithm was developed in 3 stages and adapted according to the observations made during this development:

    1. All text information was retrieved from a press release page using the `.get_text` method from `BeautifulSoup` and then the text was split into `500-character chunks`. This provided a simple starting point but produced poor results because of faulty chunk splitting and the presence of generic footers.
    2. All text information was retrieved from a press release page using the `.get_text` method from `BeautifulSoup` and then the text was split into chunks of one or multiple sentences using a tokenizer from the `nltk` library. While this avoided the issue of splitting mid-sentence, the results were still not great.
    3. **(BEST SOLUTION)** Instead of trying to split the information ourselves we can use the content split already defined in the page and created by the article's author. We can observe that a press release content is already split into headers, paragraphs, and tables:

       -add image here-
       
       If we use this observation we automatically get a simple semantic splitting of the press release information without needing to develop this splitting ourselves. As for the tables from the press releases, they are parsed into strings using Python's `tabulate` library
       
  - The press release information is saved locally in a `json` file with this format:
```
{
    "title": "That's how it works automatically: Secure sovereign business automation for Europe | Deutsche Telekom",
    "date": "05-09-2023",
    "author": "Kathrin Langkamp",
    "link": "https://www.telekom.com/en/media/media-information/archive/that-s-how-it-works-automatically-secure-sovereign-business-automation-for-europe-1039250",
    "content": [
        "T-Systems and UiPath Partnership: Business automation based on European standards, such as GDPRPartnership ensures data is stored in European data centersFirst process automation for 'Deutschlandticket'",
        "Transatlantic cooperation for best customer solutions: TheITservice provider T-Systems, subsidiary of Telekom and a leading enterprise automation software company, UiPath (NYSE: PATH) have entered into a partnership and  will deliver automation at scale according to European standards.",
        ...
    ]
```

### 2. Data Ingestion
  - We create a vector DB in PostgreSQL where we will save the relevant information from each press release: title, content, content embedding, author, published date, and URL
  - We iterate over each press release `json` file and we build embeddings for each document chunk based on the `content` of that chunk
  - The contents of the press release are embedded using a simple, open-source embedding model from the `sentence-transformer` library which can be run locally ([all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2))

### 3. Retrieval
1. The user provides a question (e.g., `"What are the AI initiatives at Deutsche Telekom?"`)
2. This question is embedded using the same embedding model from the data ingestion phase
3. The `top_k` most similar document chunks are retrieved from the vector DB
4. The document chunks with a similarity score under a certain set threshold are discarded. This helps us cover the cases when a completely irrelevant question is asked (e.g., `"What is the square root of pi?"`)

### 4. Generation
1. Using the retrieved relevant document chunks from the previous step we construct a prompt which presents the task to the LLM and the context
2. A call to an OpenAI LLM model is made and the LLM's response is returned

### 5. Interactive Streamlit App
- The user is presented with a simple Streamlit web app where they can input a question, press a button, and receive a response
- If the question is not related to Deutsche Telekom's press releases then the user will be shown the following message: `No relevant information found in the press releases for your query.`
- The user can change the values for the `top_k` and `similarity_threshold` parameters in order to fine-tune what is returned from the vector DB
- The retrieved `top_k` chunks are shown as a debugging step


## Future improvements

 - **Systematic Evaluation**: Create a test set of questions and answers to formally evaluate and compare different LLMs (e.g., GPT-4o, Claude 3.5), embedding models, and prompts
 - **Add User Feedback Loop**: Implement a simple "thumbs up/down" feature in the UI to collect feedback on answer quality, which can be used to improve the system over time
 - **Improve Scraping Robustness**: Replace requests with a stealthier, asynchronous library (e.g., [rnet](https://github.com/0x676e67/rnet)) to prevent being blocked and to speed up the process. can also use something like [Camoufox](https://github.com/daijro/camoufox) to get valid cookies and other parameters before running the scraping script
 - **Add Date-Based Scraping**: Add a feature to the scraper to fetch all press releases within a specific date range instead of getting the last X press releases
 - **Refactor to Object-Oriented Design**: Right now the code is written in the procedural programming paradigm (i.e., a bunch of functions and no classes). It's the simplest and cleanest approach for a starting point but the code might have to be adapted to the standards of the code base it will slot into (most likely OOP)
 - **Better logging**: As a simple starting point, `print` statements are often good enough. But we might have to replace them with a proper logging library (e.g., `logging` library from Python). Also log things like user questions, processing times, LLM responses, retrieved chunks, etc. to an ElasticSearch index
 - **Better error handling**: Add more `try...except` blocks around API calls and database interactions to handle network failures or other potential issues more gracefully
 - **Better documentation**: Refactor comments and function documentation to make it more explicit
 - **Error handling**: Save inputs which produce errors to a `RabbitMQ` queue such that we can analyze the errors and process the messages after fixing the errors
