import requests
from tests.conftest import USER_PASSWORD

def test_upload_download_delete_files(client, user):
    # login
    data = client.post('/auth/token', data={'username': user.email, 'password': USER_PASSWORD})
    headers = {
        "Authorization": f"Bearer {data.json()['access_token']}"
    }

    # upload files
    dummy_files = [
        ("files", ("testfile1.txt", b"Content of test file 1", "text/plain")),
        ("files", ("testfile2.txt", b"Content of test file 2", "text/plain")),
        ("files", ("testfile3.txt", b"Content of test file 3", "text/plain"))
    ]
    response = client.post("/users/documents/upload", files=dummy_files, headers=headers)

    # assert successful upload
    assert response.status_code == 200
    assert len(response.json()["failed_files"]) == 0
    assert len(response.json()["uploaded_files"]) == len(dummy_files)
    
    # check documents list
    response = client.get("/users/documents/list", headers=headers)
    file_info_list = [{"filename": file[1][0], "content_type": file[1][2], "error": None} for file in dummy_files]
    assert response.status_code == 200
    assert len(response.json()["files"]) == len(dummy_files)
    assert response.json()["files"] == file_info_list

    # download documents
    download_links = []
    for file in dummy_files:
        response = client.get(f"/users/documents/download/{file[1][0]}", headers=headers)
        assert response.status_code == 200
        download_link = response.json().get("download_link")
        download_links.append(download_link)
    
    for file, download_link in zip(dummy_files, download_links):
        download_response = requests.get(download_link)
        assert download_response.status_code == 200
        downloaded_content = download_response.content
        assert downloaded_content == file[1][1], f"The downloaded content does not match for {file[1][0]}."

    # delete documents
    file_name_list = {"file_names": [file[1][0] for file in dummy_files]}
    response = client.post("/users/documents/delete-multiple", headers=headers, json=file_name_list)
    
    # assert successful deletion
    assert response.status_code == 200
    assert len(response.json()["failed_files"]) == 0
    assert len(response.json()["deleted_files"]) == len(dummy_files)

    # check documents list
    response = client.get("/users/documents/list", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["files"]) == 0
    