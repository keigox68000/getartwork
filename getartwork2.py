import os
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import re


# 🔧 タイトル・アーティストのクリーンアップ（検索クエリ用）
def clean_title(text):
    return re.sub(r"[’'\"&()]", "", text)


# 🔧 ファイル名として使えない文字を安全な文字に置換
def sanitize_filename(filename):
    """
    ファイル名として使用できない文字をアンダースコアに置換します。
    対象文字: \ / : * ? " < > |
    """
    return re.sub(r'[\\/:*?"<>|]', "_", filename)


# ✅ `.env` ファイルを読み込む
load_dotenv("config.env")

# ✅ 環境変数を取得
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# ✅ 認証情報がない場合はエラー
if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise ValueError("❌ Spotify API の Client ID または Secret が設定されていません！")

# ✅ Spotify API 認証
sp = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET
    )
)

# ✅ 設定
LIST_ALBUMS = "list.txt"  # アルバムリスト（アルバム名 / アーティスト名）
LIST_TRACKS = "list2.txt"  # 曲リスト（曲名 / アーティスト名）
IMG_FOLDER = "img"  # 画像保存フォルダ

# ✅ imgフォルダが存在しない場合は作成
if not os.path.exists(IMG_FOLDER):
    os.makedirs(IMG_FOLDER)


# ✅ アーティスト名が一致するアイテムを検索結果から取得
def find_matching_item(items, target_artist):
    target = target_artist.lower()
    for item in items:
        for artist in item.get("artists", []):
            artist_name = artist["name"].lower()
            if target in artist_name or artist_name in target:
                return item
    return None


# ✅ リストファイルを処理する関数
def process_list(file_name, search_type):
    if not os.path.exists(file_name):
        print(f"⚠️ {file_name} が見つかりません。スキップします。")
        return

    with open(file_name, "r", encoding="utf-8") as file:
        entries = [line.strip() for line in file if line.strip()]  # 空行を除去

    for entry in entries:
        try:
            name, artist_name = entry.split(" / ")

            # 🔧 前処理（記号除去）
            cleaned_name = clean_title(name)
            cleaned_artist = clean_title(artist_name)

            album_info = None  # album_infoを初期化

            if search_type == "album":
                # 🔍 アルバм検索（最大5件取得 → アーティスト名一致チェック）
                query = f"{cleaned_name} {cleaned_artist}"
                result = sp.search(q=query, type="album", limit=5)
                matched = find_matching_item(result["albums"]["items"], cleaned_artist)

                if matched:
                    album_info = matched
                else:
                    print(
                        f"⚠️ {name} のアルバムアートワークが見つかりませんでした（アーティスト一致なし）。"
                    )
                    continue

            elif search_type == "track":
                # 🔍 曲検索 → その曲のアルバムアートを取得（最大5件取得）
                query = f"{cleaned_name} {cleaned_artist}"
                result = sp.search(q=query, type="track", limit=5)
                matched_track = find_matching_item(
                    result["tracks"]["items"], cleaned_artist
                )

                if matched_track:
                    album_info = matched_track["album"]
                else:
                    print(
                        f"⚠️ {name} のアルバムアートワークが見つかりませんでした（アーティスト一致なし）。"
                    )
                    continue

            # 🎨 アルバム名と画像URLを取得
            album_name = album_info["name"]
            image_url = album_info["images"][0]["url"]

            # 🔧 ファイル名をサニタイズ（安全な名前に変換）
            sanitized_artist_name = sanitize_filename(artist_name)
            sanitized_album_name = sanitize_filename(album_name)
            image_path = os.path.join(
                IMG_FOLDER, f"{sanitized_artist_name}_{sanitized_album_name}.jpg"
            )

            # 📥 画像をダウンロード
            img_data = requests.get(image_url).content
            with open(image_path, "wb") as img_file:
                img_file.write(img_data)

            print(
                f"✅ {name}（{album_name}）のアートワークを取得しました: {image_path}"
            )

        except Exception as e:
            print(f"❌ {entry} の処理中にエラーが発生しました: {e}")


# ✅ `list.txt`（アルバム検索）を処理
process_list(LIST_ALBUMS, "album")

# ✅ `list2.txt`（曲検索）を処理
process_list(LIST_TRACKS, "track")

print("🎵 すべてのアルバムアートワークの取得が完了しました。")
