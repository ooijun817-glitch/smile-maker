# 絵の出どころとライセンス

## 使える素材(メトロポリタン美術館 Open Access / パブリックドメイン)
Met の Open Access プログラムにより、画像はパブリックドメイン(CC0)として公開されている。
Open Access について:https://www.metmuseum.org/policies/image-resources

| # | 作品 | 作者 | 画像ファイル | 目録での確認 |
| --- | --- | --- | --- | --- |
| 2 | 神奈川沖浪裏 Under the Wave off Kanagawa | 葛飾北斎 | https://images.metmuseum.org/CRDImages/as/original/DP130155.jpg | 作品 45434 / JP1847、パブリックドメイン ✓ |
| 3 | 凱風快晴(赤富士)South Wind, Clear Sky | 葛飾北斎 | https://images.metmuseum.org/CRDImages/as/original/DP141062.jpg | 同じ版画の別の1枚(作品 55736 / JP2960、画像 DP141053)はパブリックドメイン ✓。DP141062 の作品番号は未照合 |
| 5 | 駿州江尻 Ejiri in Suruga Province | 葛飾北斎 | https://images.metmuseum.org/CRDImages/as/original/DP140977.jpg | 同じ版画の別の2枚(作品 55735 / JP2953、作品 56988 / JP2553)はパブリックドメイン ✓。DP140977 の作品番号は未照合 |
| 6 | 三代目大谷鬼次の江戸兵衛 Kabuki Actor Ōtani Oniji III as Yakko Edobei | 東洲斎写楽 | https://images.metmuseum.org/CRDImages/as/original/DP130228.jpg | 作品 37358 / JP2822、パブリックドメイン ✓ |
| 7 | 木曽海道六拾九次之内 洗馬 | 歌川広重 | https://images.metmuseum.org/CRDImages/as/original/DP120447.jpg | 作品番号は未照合(ukiyo-e.org の Met 収蔵品の索引で「Senba Station」として見つけた) |

- 取得日:2026-10-28。どれも絵柄が合っていることを目で確かめた。
- 「目録での確認」は Met の公式データ(collectionapi.metmuseum.org)で isPublicDomain を確かめたもの。
- 赤富士・江尻・洗馬は同じ版画が Met に複数あり、状態のよい1枚を選んだ。選んだ画像の作品番号は、
  Met の検索機能が使えなかったため未照合。どれも Met の Open Access の画像として公開されている。

## 仮の素材(GitHub に保存しない。work/sources/ に置く)

| # | 作品 | 今の画像 | 問題 | 次にやること |
| --- | --- | --- | --- | --- |
| 4 | 鳳凰図屏風(葛飾北斎、1835年) | いただいた画像 1600×245 | 小さくてぼやける。所蔵はボストン美術館(11.7433)で、利用条件は「個人・非営利の範囲」と見られるが、規約本文は未確認 | 美術館のページから大きい画像をダウンロードし、規約を確かめる |
| 1 | 北斎肖像 | Pinterest の画像 683×972 | 出どころ不明。小さい | 所蔵先(図書館・美術館)の大きい画像を探す |

## 加工
`tools/prepare_images.py` で次の加工だけをしている。絵そのものには手を加えていない。
- 紙の余白を切り落とし、印刷面だけにした
- 7枚を 1920×1296 にそろえた。横長の絵は端をわずかに切り、縦長の絵(写楽・北斎肖像)は
  中央に置いて左右を絵の地の色で埋めた。鳳凰図屏風は頭と胸のあたりを切り出した

## AI で作った動画について
`segments/` と `ios/HokusaiLoop/hokusai-loop.mp4` は、上の絵をもとに Kling(AI)で作った動画。
絵の線や形は AI が描き直したもので、原画そのものではない。
