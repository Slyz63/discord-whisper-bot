import discord
import whisper
import os

# --------------------------------------------------
# 初期設定
# --------------------------------------------------
# 環境変数からDiscord BOTのトークンを読み込む
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')

# Whisperのモデルを選択（tiny, base）
# Renderの無料プランでは 'tiny' または 'base' を推奨します。
MODEL_SIZE = 'base'
# --------------------------------------------------


# BOTの接続設定
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Whisperのモデルをロード
# 初回起動時にモデルのダウンロードが行われます
print(f"Whisperの '{MODEL_SIZE}' モデルをロード中...")
model = whisper.load_model(MODEL_SIZE)
print("モデルのロードが完了しました。")


@client.event
async def on_ready():
    """BOTが起動したときに実行される処理"""
    print(f'{client.user} としてログインしました')


@client.event
async def on_message(message):
    """メッセージが投稿されたときに実行される処理"""
    # BOT自身のメッセージは無視
    if message.author == client.user:
        return
    
    # トークンが設定されていない場合はエラーメッセージを出して処理を中断
    if not DISCORD_TOKEN:
        print("エラー: DISCORD_TOKENが設定されていません。")
        return

    # 添付ファイルがあるかチェック
    if message.attachments:
        for attachment in message.attachments:
            # 音声ファイル形式を簡易的にチェック（拡張子）
            supported_extensions = ('.mp3', '.wav', '.ogg', '.flac', '.m4a', '.mp4', '.mov')
            if attachment.filename.lower().endswith(supported_extensions):
                
                filepath = f"./{attachment.filename}"

                try:
                    # 処理中であることをユーザーに通知
                    await message.channel.send(f"**`{attachment.filename}`** の文字起こしを開始します... 🤖")

                    # 音声ファイルをダウンロードして保存
                    await attachment.save(filepath)

                    # Whisperで文字起こしを実行
                    # fp16=False はCPUでの実行時に推奨される設定です
                    result = model.transcribe(filepath, fp16=False, language='ja')
                    transcribed_text = result['text']

                    # 結果をDiscordに送信
                    if transcribed_text:
                        # 長文の場合は2000文字ごとに分割して送信
                        for i in range(0, len(transcribed_text), 2000):
                             await message.reply(transcribed_text[i:i+2000], mention_author=False)
                    else:
                        await message.reply("文字を検出できませんでした。", mention_author=False)

                except Exception as e:
                    await message.reply(f"エラーが発生しました: {e}", mention_author=False)
                    print(f"エラー詳細: {e}")
                
                finally:
                    # 処理が終わったら一時ファイルを必ず削除
                    if os.path.exists(filepath):
                        os.remove(filepath)

# BOTを実行
client.run(DISCORD_TOKEN)
