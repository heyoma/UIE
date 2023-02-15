#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
from transformers import AutoTokenizer


def fix_unk_from_text(span, text, unk='<unk>', tokenizer=None):
    """Fixing unknown tokens `unk` in the generated expression
    Args:
        span (str): generated span
        text (str): raw text
        unk (str, optional): symbol of unk token
        tokenizer (Tokenizer, optional): the tokenizer
    Returns:
        fixed span
    """
    if tokenizer is not None:
        return fix_unk_from_text_with_tokenizer(span,
                                                text,
                                                unk=unk,
                                                tokenizer=tokenizer)
    else:
        return fix_unk_from_text_without_tokenizer(span, text, unk=unk)


def match_sublist(the_list, to_match: str, id2token):
    """ Find sublist in the whole list
    Args:
        the_list (list(str)): the whole list
            - [1, 2, 3, 4, 5, 6, 1, 2, 4, 5]
        to_match (list(str)): the sublist
            - [1, 2]
    Returns:
        list(tuple): matched (start, end) position list
            - [(0, 1), (6, 7)]
    """
    decoded_text = ""
    decoded_offset_mapping = []
    offset = 0
    tokens = []
    for i, tid in enumerate(the_list):
        token = id2token[tid].replace("▁", "")
        tokens.append(token)
        decoded_text += token
        for c in token:
            decoded_offset_mapping.append(i)
        offset = offset + len(token)
    index = decoded_text.find(to_match)
    if index == -1:
        return None
    matched = [decoded_offset_mapping[index], decoded_offset_mapping[index + len(to_match) - 1]]
    return matched


def fix_unk_from_text_with_tokenizer(span, text, unk='<unk>', tokenizer=None):
    id2token = {v: k for k, v in tokenizer.vocab.items()}

    tokenized = tokenizer(text,
                          add_special_tokens=False,
                          return_token_type_ids=None,
                          return_offsets_mapping=True)

    tokenized_text, offset_mapping = tokenized["input_ids"], tokenized["offset_mapping"]

    matched = match_sublist(tokenized_text, span, id2token)
    if not matched:
        return fix_unk_from_text_without_tokenizer(span, text, unk)

    true_offset = [offset_mapping[matched[0]][0], offset_mapping[matched[-1]][-1]]
    fixed_span = text[true_offset[0]: true_offset[1]]
    match_reversed = r'\s*\S+\s*'.join([clean_wildcard(item.strip()) for item in span.split(unk)])
    fixed_span = re.search(match_reversed, fixed_span)
    if not fixed_span:
        return span
    return fixed_span.group().strip()


def clean_wildcard(x):
    sp = ".*?()[]+"
    return re.sub("(" + "|".join([f"\\{s}" for s in sp]) + ")", "\\\\\g<1>", x)

def fix_unk_from_text_without_tokenizer(span, text, unk='<unk>'):
    """
    Find span from the text to fix unk in the generated span
    从 text 中找到 span，修复span

    Example:
    span = "<unk> colo e Bengo"
    text = "At 159 meters above sea level , Angola International Airport is located at Ícolo e Bengo , part of Luanda Province , in Angola ."

    span = "<unk> colo e Bengo"
    text = "Ícolo e Bengo , part of Luanda Province , in Angola ."

    span = "Arr<unk> s negre"
    text = "The main ingredients of Arròs negre , which is from Spain , are white rice , cuttlefish or squid , cephalopod ink , cubanelle and cubanelle peppers . Arròs negre is from the Catalonia region ."

    span = "colo <unk>"
    text = "At 159 meters above sea level , Angola International Airport is located at e Bengo , part of Luanda Province , in Angola . coloÍ"

    span = "Tarō As<unk>"
    text = "The leader of Japan is Tarō Asō ."

    span = "Tar<unk> As<unk>"
    text = "The leader of Japan is Tarō Asō ."

    span = "<unk>Tar As<unk>"
    text = "The leader of Japan is ōTar Asō ."
    """
    if unk not in span:
        return span



    match = r'\s*\S+\s*'.join([clean_wildcard(item.strip()) for item in span.split(unk)])
    result = re.search(match, text)
    # print(result.group().strip())
    match_reversed = r'\s*\S+?\s*'.join([clean_wildcard(item.strip()[::-1]) for item in span.split(unk)][::-1])
    result_reversed = re.search(match_reversed, text[::-1])
    if not result_reversed:
        return span
    return result_reversed.group()[::-1].strip()


def test_fix_unk_from_text():
    span_text_list = [
        ("<unk> colo e Bengo",
         "At 159 meters above sea level , Angola International Airport is located at Ícolo e Bengo , part of Luanda Province , in Angola .",
         "Ícolo e Bengo"),
        ("<unk> colo e Bengo",
         "Ícolo e Bengo , part of Luanda Province , in Angola .",
         "Ícolo e Bengo"),
        ("Arr<unk> s negre",
         "The main ingredients of Arròs negre , which is from Spain , are white rice , cuttlefish or squid , cephalopod ink , cubanelle and cubanelle peppers . Arròs negre is from the Catalonia region .",
         "Arròs negre"),
        ("colo <unk>",
         "At 159 meters above sea level , Angola International Airport is located at e Bengo , part of Luanda Province , in Angola . coloÍ",
         "coloÍ"),
        ("Tarō As<unk>", "The leader of Japan is Tarō Asō .", "Tarō Asō"),
        ("Tar<unk> As<unk>", "The leader of Japan is Tarō Asō .", "Tarō Asō"),
        ("<unk>Tar As<unk>", "The leader of Japan is ōTar Asō .", "ōTar Asō"),
        ("Atatürk Monument ( <unk> zmir )",
         "The Atatürk Monument ( İzmir ) can be found in Turkey .",
         "Atatürk Monument ( İzmir )"),
        ("The Atatürk Monument [ <unk> zmir ]",
         "The Atatürk Monument [ İzmir ] can be found in Turkey .",
         "The Atatürk Monument [ İzmir ]")
    ]

    for span, text, gold in span_text_list:
        print(span, '|', fix_unk_from_text(span, text))
        assert fix_unk_from_text(span, text) == gold


if __name__ == "__main__":
    span = "河北省<unk>源県"
    # span = "<unk>雪奇缘"
    text = "続いて11月3日には河北省淶源県の八路軍晋察冀軍区第一分区との戦闘を計画した。"
    # text = "她从2013年2月开始吧自己拍摄的视频传至网络。2014年7-8月左右，" \
    #        "她与25个迪士尼角色合唱电影《冰雪奇缘》主题曲《Let it go》的视频走红，成为热门话题，她也被称为智能手机的歌姬。"

    tokenizer = AutoTokenizer.from_pretrained("E:\\work\\semeval\\code\\uie-server\\hf_models\\t5-base-ja")
    result = fix_unk_from_text(span, text, tokenizer=tokenizer)
    print(result)
