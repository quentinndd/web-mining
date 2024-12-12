d
import wikipedia
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string
import nltk
import json

# Configurer Wikipédia et NLTK
wikipedia.set_lang("en")
nltk.download('punkt')
nltk.download('stopwords')

# Préparer les stopwords et le stemmer
stop_words = list(set(stopwords.words('english'))) + ["'s"]
stem = nltk.stem.SnowballStemmer("english")

# Fonction pour extraire les tokens
def extract_tokens(text):
    text = text.lower()
    tokens = word_tokenize(text)
    tokens = [token for token in tokens if token not in string.punctuation]
    tokens = [token for token in tokens if token not in stop_words]
    tokens = [stem.stem(token) for token in tokens]
    return tokens

# Fonction pour obtenir les n tokens les plus fréquents
def get_top_tokens(content, n=20):
    tokens = extract_tokens(content)
    token_counts = {}
    for token in tokens:
        if token in token_counts:
            token_counts[token] += 1
        else:
            token_counts[token] = 1
    sorted_tokens = sorted(token_counts.items(), key=lambda item: item[1], reverse=True)
    top_tokens = [item[0] for item in sorted_tokens[:n]]
    return set(top_tokens)

# Fonction pour vérifier la pertinence en fonction des tokens principaux
def is_relevant_based_on_top_tokens(top_tokens, linked_summary, threshold=5):
    linked_tokens = extract_tokens(linked_summary)
    common_tokens = [token for token in linked_tokens if token in top_tokens]
    return len(common_tokens) >= threshold

# Sauvegarder les données dans un fichier JSON
def save_data(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

# Fonction pour stocker les contenus des pages
def store_content(page_title, page_content, content_storage, content_file):
    if page_title not in content_storage:
        content_storage[page_title] = page_content
        save_data(content_file, content_storage)  # Sauvegarder immédiatement
        print(f"Content stored: {page_title}")

# Fonction pour stocker les liens entre les pages
def store_links(source_page, linked_page, link_storage, link_file):
    if source_page not in link_storage:
        link_storage[source_page] = []
    if linked_page not in link_storage[source_page]:
        link_storage[source_page].append(linked_page)
        save_data(link_file, link_storage)  # Sauvegarder immédiatement
        print(f"Link stored: {source_page} -> {linked_page}")

# Fonction principale pour le scraping BFS
def bfs_scrape(start_page, max_depth=3, content_file='content.json', link_file='links.json'):
    visited = set()  # Set des pages visitées
    queue = [(start_page, 0)]  # File d'attente initiale (page, profondeur)
    content_storage = {}  # Stockage des contenus des pages
    link_storage = {}  # Stockage des liens entre pages

    # Obtenir les top tokens de la page de départ
    main_page = wikipedia.WikipediaPage(start_page)
    top_tokens = get_top_tokens(main_page.content, n=20)
    print(f"Top Tokens for {start_page}: {top_tokens}\n")

    while queue:
        # Retirer la première page de la queue
        current_page, depth = queue.pop(0)

        # Vérifier si la profondeur maximale est atteinte
        if depth > max_depth:
            continue

        # Marquer la page comme visitée
        if current_page in visited:
            continue
        visited.add(current_page)

        try:
            # Charger la page actuelle
            print(f"Scraping: {current_page} (Depth {depth})")
            page = wikipedia.WikipediaPage(current_page)

            # Vérifier si la page est pertinente
            if is_relevant_based_on_top_tokens(top_tokens, page.summary, threshold=5):
                # Stocker le contenu de la page
                store_content(current_page, page.content, content_storage, content_file)

                # Parcourir les liens pertinents et les stocker
                for link in page.links:
                    if link not in visited:
                        try:
                            linked_page = wikipedia.WikipediaPage(link)

                            # Vérifier si le lien est pertinent
                            if is_relevant_based_on_top_tokens(top_tokens, linked_page.summary, threshold=5):
                                # Stocker le lien pertinent
                                store_links(current_page, link, link_storage, link_file)
                                # Stocker directement le contenu de la page liée
                                store_content(link, linked_page.content, content_storage, content_file)
                                # Ajouter à la file d'attente
                                queue.append((link, depth + 1))

                        except wikipedia.exceptions.DisambiguationError:
                            print(f"DisambiguationError: {link} has multiple meanings.")
                        except wikipedia.exceptions.PageError:
                            print(f"PageError: {link} does not exist.")
                        except wikipedia.exceptions.WikipediaException as e:
                            print(f"WikipediaException: {link} caused an error. Details: {e}")

        except wikipedia.exceptions.DisambiguationError:
            print(f"DisambiguationError: {current_page} has multiple meanings.")
        except wikipedia.exceptions.PageError:
            print(f"PageError: {current_page} does not exist.")
        except wikipedia.exceptions.WikipediaException as e:
            print(f"WikipediaException: {current_page} caused an error. Details: {e}")

    print("\nScraping completed.")

# Lancer le scraping
bfs_scrape("Diversity (business)", max_depth=2, content_file='content.json', link_file='links.json')

