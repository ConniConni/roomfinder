FROM postgis/postgis:16-3.4

# ロケールは生成するが、LANGは英語(en_US)に設定
RUN localedef -i ja_JP -c -f UTF-8 -A /usr/share/locale/locale.alias ja_JP.UTF-8

# メッセージを英語にする
ENV LANG en_US.utf8