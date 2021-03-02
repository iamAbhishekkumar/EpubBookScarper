from bs4 import BeautifulSoup
import requests 
from flask import Flask, send_file, jsonify,render_template
from helper import remove_tags
import os

app = Flask("__name__",template_folder='templates')


@app.route("/getFile/<book_id>")
def getFile(book_id):
    file_url = "https://www.epubbooks.com/book/" + book_id
    with requests.session() as s:
        response1 = s.get("https://www.epubbooks.com/login")
        soup3 = BeautifulSoup(response1.text, 'html5lib')
        payload = {
            "authenticity_token": soup3.find("input", attrs={"type": "hidden"})['value'],
            "user[email]": os.environ['email'],
            "user[password]": os.environ['password'],
            "user[remember_me]": "0",
            "commit": "Sign+in"
        }
        r = s.post("https://www.epubbooks.com/login", data=payload)
        if r.status_code == 200:
            response = s.get(file_url)
            soup2 = BeautifulSoup(response.text, 'html5lib')
            download_url = "https://www.epubbooks.com/" + str(
                soup2.select("li.clearfix:nth-child(1) > a:nth-child(1)")[0]['href'])
            download_book = s.get(download_url)
            open("book.epub", "wb").write(download_book.content)
            path = "book.epub"
            return send_file(path, as_attachment=True)
        else:
            return "error..check your network"


@app.route("/getHomePage")
def get_home_page():
    url = "https://www.epubbooks.com"
    response = requests.get(url)
    print(response.status_code)
    soup = BeautifulSoup(response.text, 'html5lib')
    featured_books, new_ebook, today_special = [], [], []

    for book in soup.findAll("div", attrs={"class": "col-xs-6 col-sm-3"}):
        featured_books.append({
            "book_id": str(book.find("a")['href']).replace("/book/", ""),
            "img_src": book.find("img")['src'],
            "name": book.find("img")['alt'].split("by")[0].strip(),
            "author": book.find("img")['alt'].split("by")[1].strip()

        })
    for book in soup.findAll("div", attrs={"class": "col-md-6"}):
        new_ebook.append({
            "name": remove_tags(str(book.find("h4").find('a'))),
            "author": remove_tags(str(book.find("h4").find('span'))),
            "book_id": str(book.find("a")['href']).replace("/book/", ""),
            "img_src": str(book.find("img")['src']).replace("_thumb", ""),

        })

    for special_book in soup.findAll("div", attrs={"class": "col-xs-4 col-sm-3 col-md-2"}):
        today_special = {
            "book_id": str(special_book.find("a")['href']).replace("/book/", ""),
            "img_src": special_book.find("img")['src'],
            "name": remove_tags(str(soup.select(".col-xs-8 > h2:nth-child(1) > a:nth-child(1)")[0])),
            "author": remove_tags(str(soup.select(".col-xs-8 > h3:nth-child(2)")[0])),
            "description": remove_tags(str(soup.select(".col-xs-8 > p:nth-child(3)")[0])).replace("Read More »","")
        }

    result = {
        "featuredBooks": featured_books,
        "newBooks": new_ebook,
        "todaySpecial": today_special
    }
    return jsonify(result)


@app.route("/getCategories")
def getSubjectsAndCategories():
    url = "https://www.epubbooks.com/subjects"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html5lib')
    result = []
    for subject in soup.findAll("div", attrs={"class": "col-md-6"}):
        result.append({
            "href": str(subject.find("a")['href']).replace("/subject", ""),
            "title": remove_tags(str(subject)).strip().replace("&amp;", "&")
        })
    return jsonify(result)


@app.route("/getSubjects/<subject>/<page>")
def getSubjects(subject, page):
    url = "https://www.epubbooks.com/subject/" + subject + f"?page={page}"
    response = requests.get(url)
    result = []
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html5lib')
        for i in soup.findAll("li", attrs={"class": "media"}):
            result.append({
                "img_src": str(i.find("img")['src']).replace("_thumb", ""),
                "href": str(i.find("a")['href']),
                "name": remove_tags(str(i.find("h2").find("a"))),
                "author": remove_tags(str(i.find("h2").find("span"))),
            })
    return jsonify(result)


@app.route("/getBookDetails/<book_id>")
def getBookDetails(book_id):
    url = "https://www.epubbooks.com/book/" + book_id
    response = requests.get(url)
    result = []
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html5lib')
        excerpt = ""
        for para in soup.findAll("div", attrs={"class": "col-md-6", "itemprop": "text"})[0].findAll("p"):
            excerpt += remove_tags(str(para)).strip() + "\n"
        genres = []
        for genre in soup.findAll("span", attrs={"itemprop": "genre"}):
            genres.append(remove_tags(str(genre)).strip().replace("&amp;", "&"))
        result.append({
            "rating": remove_tags(str(soup.select("span.text-muted")[0])),
            "genre": genres,
            "description": remove_tags(str(soup.select("div.container:nth-child(2) > div:nth-child(2) > "
                                                       "div:nth-child(3) > p:nth-child(1)")[0])),
            "excerpt": excerpt,
        })
    return jsonify(result)


@app.route("/getAuthorDetails/<author_id>")
def getAuthorDetails(author_id):
    url = "https://www.epubbooks.com/author/" + author_id
    response = requests.get(url)
    result = []
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html5lib')
        available_ebooks = []
        for book in soup.findAll("div", attrs={"class": "author-pubs-widget"}):
            available_ebooks.append({
                "img_src": str(book.find("img")['src']).replace("_thumb", ""),
                "book_id": str(book.find("a")['href'].replace("/book/", "")),
                "name": remove_tags(str(book.find("h4").find("a"))),
                "year": remove_tags(str(book.find("h4").find("span")))
            })
        result.append({
            "description": remove_tags(
                str(soup.select("div.row:nth-child(4) > div:nth-child(2) > div:nth-child(1)")[0])).strip(),
            "available_books": available_ebooks,

        })

    return jsonify(result)


@app.route("/search/<keyword>")
def search(keyword):
    keyword = str(keyword).replace(" ", "+")
    url = "https://www.epubbooks.com/search?q=" + keyword
    response = requests.get(url)
    result = []
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html5lib')
        for i in soup.findAll("li", attrs={"class": "media"}):
            result.append({
                "img_src": str(i.find("img")['src']).replace("_thumb", ""),
                "href": str(i.find("a")['href']),
                "name": remove_tags(str(i.find("h4").find("a"))),
                "author": remove_tags(str(i.find("h4").find("span"))),
            })
    return jsonify(result)

@app.route("/help")
def help():
    return render_template('index.html')

    
if __name__ == '__main__':
    app.run(debug=True)
