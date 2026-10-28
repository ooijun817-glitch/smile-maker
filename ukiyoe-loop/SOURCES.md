# 絵の出どころとライセンス

3枚とも、メトロポリタン美術館(The Metropolitan Museum of Art, New York)所蔵の
葛飾北斎『冨嶽三十六景』より。Met の Open Access プログラムにより、画像は
パブリックドメイン(CC0)として公開されている。

| 使う場面 | 作品 | 英題(Met での表記の通称) | 画像ファイル |
| --- | --- | --- | --- |
| 区間1 | 神奈川沖浪裏 | Under the Wave off Kanagawa (The Great Wave) | https://images.metmuseum.org/CRDImages/as/original/DP130155.jpg |
| 区間2 の着地点 | 凱風快晴(赤富士) | South Wind, Clear Sky (Gaifū kaisei), also known as Red Fuji | https://images.metmuseum.org/CRDImages/as/original/DP141062.jpg |
| 区間3 の着地点 | 駿州江尻 | Ejiri in Suruga Province (Sunshū Ejiri) | https://images.metmuseum.org/CRDImages/as/original/DP140977.jpg |

- Open Access について:https://www.metmuseum.org/policies/image-resources
- 取得日:2026-10-28。3枚とも上の URL から直接取得し、絵柄が合っていることを目で確かめた。
- 作品ページ:神奈川沖浪裏 https://www.metmuseum.org/art/collection/search/45434 、
  凱風快晴は https://www.metmuseum.org/art/collection/search/55736 、
  駿州江尻は https://www.metmuseum.org/art/collection/search/55735 または 56988 と見られる。
  作業環境から Met の作品ページに接続できないため、作品ページの番号と所蔵番号は未照合。
  赤富士の画像番号は ukiyo-e.org の Met 収蔵品の索引で調べた。江尻は Met の画像番号の近くを
  順に見て探した(DP140977・DP141030・DP141046 の3枚があり、収集家の印や折れ目のない
  DP140977 を選んだ)。

## 加工
`tools/prepare_images.py` で次の加工だけをしている。絵そのものには手を加えていない。
- 赤富士・江尻は紙の余白を切り落とし、印刷面だけにした
- 3枚を 1920×1296 にそろえた(縦横比を合わせるため、中央を残して端をわずかに切った)

## AI で作った動画について
`segments/` と `ios/HokusaiLoop/hokusai-loop.mp4` は、上の絵をもとに Kling(AI)で
作った動画。絵の線や形は AI が描き直したもので、北斎の原画そのものではない。
