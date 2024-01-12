from pymongo import MongoClient
from dash import dash, dcc, html, callback, Input, Output, State

# Connect to MongoDB using the host machine's IP
client = MongoClient("mongodb://mongodb:27017/")

# Specify the MongoDB collection
db = client.NY_Project  # Replace 'ny_times' with your actual collection name
collection = db.ny_articles  # Replace 'your_collection_name' with your actual collection name

# Aggregation query to get average word count, count articles per section, and 5 newest articles
pipeline = [
    {
        '$group': {
            '_id': None,
            'average_word_count': {'$avg': '$word_count'},
            'sections': {'$push': '$news_desk'},
            'section_counts': {'$push': {'section': '$news_desk', 'count': 1}},
            'newest_articles': {'$push': {'headline': '$headline', 'web_url': '$web_url', 'pub_date': '$pub_date'}},
            'total_articles': {'$sum': 1}
        }
    },
    {
        '$unwind': '$section_counts'
    },
    {
        '$group': {
            '_id': '$section_counts.section',
            'section_count': {'$sum': '$section_counts.count'},
            'average_word_count': {'$first': '$average_word_count'},
            'newest_articles': {'$first': '$newest_articles'},
            'total_articles': {'$first': '$total_articles'}
        }
    },
]


result = list(collection.aggregate(pipeline))

# Extract total number of articles, average word count, sections with counts, and 5 newest articles
total_articles = result[0]['total_articles']
average_word_count = result[0]['average_word_count']
sections = [section['_id'] for section in result]
article_counts = [section['section_count'] for section in result]
newest_articles = result[0]['newest_articles'][:5]  # Get the 5 newest articles

# Initialize Dash app
app = dash.Dash(__name__)

# Define the layout
app.layout = html.Div(children=[
    html.H1(children='NY Times Article Statistics'),

    html.Div(children=f'Total articles: {total_articles}', style={'marginBottom': 20}),

    html.Div(children=f'The average word count is: {average_word_count:.2f}', style={'marginBottom': 20}),

    # Search bar
    html.H2("Article Search"),
    dcc.Input(id='search-input', type='text', placeholder='Enter keywords...'),

    # Create a list of links to the articles based on the search results
    html.Ul(id='search-results'),

    html.H2("Articles per Section:"),

    # Create a list of sections and counts
    html.Ul([
        html.Li(f"{section}: {count} articles") for section, count in zip(sections, article_counts)
    ]),

    html.H2("5 Latest Articles:"),

    # Create a list of links to the 5 newest articles
    html.Ul([
        html.Li(html.A(article['headline']['main'], href=article['web_url']), style={'list-style-type': 'none'}) for article in newest_articles
    ])
])

# Define callback to update search results
@app.callback(
    Output('search-results', 'children'),
    [Input('search-input', 'value')],
    prevent_initial_call=True
)
def update_search_results(search_query):
    # MongoDB query to find articles containing the search query in keywords
    search_pipeline = [
        {'$match': {'keywords.value': {'$regex': f'{search_query}', '$options': 'i'}}},
        {'$project': {'headline': '$headline.main', 'web_url': '$web_url', '_id': 0}},
        {'$limit': 5}
    ]

    search_results = list(collection.aggregate(search_pipeline))

    # Display search results as links
    result_links = [
        html.Li(html.A(result['headline'], href=result['web_url'])) for result in search_results
    ]

    return result_links

if __name__ == '__main__':
    app.run_server(debug=True)
