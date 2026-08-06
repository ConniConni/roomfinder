import requests

r = requests.get(url="http://127.0.0.1:8000/")
result = r.json()
print(result)

r_post = requests.post(url="http://127.0.0.1:8000/", json={"x": 3, "y": 4})
result_post = r_post.json()
print(result_post)


def main():
    url = "http://127.0.0.1:8000/"
    body = {"x": 3, "y": 4}

    res_get = requests.get(url)

    print(res_get.json())

    res_post = requests.post(url, json=body)
    print(res_post.json())


if __name__ == "__main__":
    main()
