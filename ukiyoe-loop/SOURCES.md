# 絵の出どころとライセンス

## 使える素材(メトロポリタン美術館 Open Access / パブリックドメイン)
Met の Open Access プログラムにより、画像はパブリックドメイン(CC0)として公開されている。
Open Access について:https://www.metmuseum.org/policies/image-resources

| # | 作品 | 作者 | 画像ファイル | 目録での確認 |
| --- | --- | --- | --- | --- |
| 1 | 神奈川沖浪裏 Under the Wave off Kanagawa | 葛飾北斎 | https://images.metmuseum.org/CRDImages/as/original/DP130155.jpg | 作品 45434 / JP1847、パブリックドメイン ✓ |
| 2 | 凱風快晴(赤富士)South Wind, Clear Sky | 葛飾北斎 | https://images.metmuseum.org/CRDImages/as/original/DP141062.jpg | 同じ版画の別の1枚(作品 55736 / JP2960、画像 DP141053)はパブリックドメイン ✓。DP141062 の作品番号は未照合 |
| 6 | 駿州江尻 Ejiri in Suruga Province | 葛飾北斎 | https://images.metmuseum.org/CRDImages/as/original/DP140977.jpg | 同じ版画の別の2枚(作品 55735 / JP2953、作品 56988 / JP2553)はパブリックドメイン ✓。DP140977 の作品番号は未照合 |
| 4 | 三代目大谷鬼次の江戸兵衛 Kabuki Actor Ōtani Oniji III as Yakko Edobei | 東洲斎写楽 | https://images.metmuseum.org/CRDImages/as/original/DP130228.jpg | 作品 37358 / JP2822、パブリックドメイン ✓ |
| 7 | 木曽海道六拾九次之内 洗馬 | 歌川広重 | https://images.metmuseum.org/CRDImages/as/original/DP120447.jpg | 作品番号は未照合(ukiyo-e.org の Met 収蔵品の索引で「Senba Station」として見つけた) |
| 8 | 東海道五拾三次之内 蒲原 夜之雪 | 歌川広重 | https://images.metmuseum.org/CRDImages/as/original/DP122189.jpg | Met 36937(パブリックドメイン)。夜空が黒い刷りを選んだ |
| 9 | 東海道五拾三次之内 日本橋 朝之景 | 歌川広重 | https://images.metmuseum.org/CRDImages/as/original/DP122174.jpg | Met 36922(パブリックドメイン) |
| 10 | 名所江戸百景 大はしあたけの夕立 | 歌川広重 | https://images.metmuseum.org/CRDImages/as/original/DP123602.jpg | Met 37386(パブリックドメイン)。縦長なので左右を地の色で埋めた |
| 11 | 東海道五拾三次之内 庄野 白雨 | 歌川広重 | https://images.metmuseum.org/CRDImages/as/original/DP122226.jpg | Met 36967(パブリックドメイン) |
| 12 | 富嶽三十六景 山下白雨 | 葛飾北斎 | https://images.metmuseum.org/CRDImages/as/original/DP141040.jpg | Met 57006(パブリックドメイン) |

- 取得日:2026-10-28。どれも絵柄が合っていることを目で確かめた。
- 「目録での確認」は Met の公式データ(collectionapi.metmuseum.org)で isPublicDomain を確かめたもの。
- 赤富士・江尻・洗馬は同じ版画が Met に複数あり、状態のよい1枚を選んだ。選んだ画像の作品番号は、
  Met の検索機能が使えなかったため未照合。どれも Met の Open Access の画像として公開されている。

## 仮の素材(GitHub に保存しない。work/sources/ に置く)

| # | 作品 | 今の画像 | 問題 | 次にやること |
| --- | --- | --- | --- | --- |
| 5 | 北斎肖像 | Pinterest の画像 683×972 | 出どころ不明。小さい | 所蔵先(図書館・美術館)の大きい画像を探す |
| 3 | 八方睨み鳳凰図(葛飾北斎、1848年、岩松院 本堂の天井画) | いただいた画像 1213×1007(Japaaan の記事の画像) | 絵そのものは著作権が切れている。写真を撮った人・提供元と利用条件は未確認 | 提供元の利用条件を確かめるか、岩松院・小布施町が公開している画像を探す |

## 加工
`tools/prepare_images.py` で次の加工だけをしている。絵そのものには手を加えていない。
- 紙の余白を切り落とし、印刷面だけにした
- 7枚を 1920×1296 にそろえた。横長の絵は端をわずかに切り、縦長や正方形に近い絵(北斎肖像・八方睨み鳳凰図・写楽)は
  中央に置いて左右を絵の地の色で埋めた

## AI で作った動画について
`segments/` と `ios/HokusaiLoop/hokusai-loop.mp4` は、上の絵をもとに Kling(AI)で作った動画。
絵の線や形は AI が描き直したもので、原画そのものではない。

## 音楽について
`ios/HokusaiLoop/hokusai-music.wav` は、`tools/make_music.py` がその場で作った音。録音や既存の曲は
使っていない。人の掛け声(`sounds/kakegoe-*.wav`)は、Figma Weave の音声 AI(Qwen-3 TTS)で作った声を
切り分けたもの。箏のような音は弦をはじいたときの倍音を重ねて作り、音階は都節音階(レ・ミ♭・ソ・ラ・シ♭)。
