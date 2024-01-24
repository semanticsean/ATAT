Delivered-To: sean@semantic-life.com
Received: by 2002:a05:612c:2b90:b0:448:dcc7:cc80 with SMTP id ip16csp1363627vqb;
        Wed, 24 Jan 2024 14:39:22 -0800 (PST)
X-Received: by 2002:a05:6602:4f1a:b0:7bc:3cb6:f074 with SMTP id gl26-20020a0566024f1a00b007bc3cb6f074mr159229iob.39.1706135961787;
        Wed, 24 Jan 2024 14:39:21 -0800 (PST)
ARC-Seal: i=1; a=rsa-sha256; t=1706135961; cv=none;
        d=google.com; s=arc-20160816;
        b=a7i3Nognz2yDr/Brs/1igYlchTNm+E3aaPD9Q24Rjklw8one49cp6tDQz+gJUQ7zUj
         0i2urG5uVhzX9mLiU3e63OYL6USbDu0BAx+sGnhHzn96rbA5WOF7gRg5EQj5UHFPAl2W
         W/p1HHtFvaqmP9pTV4YuOc4KJExYpTabLqVeVHlMJkiB7NHLbR/7rqhjeCKe5cqft2rA
         oXux1UjY8SUhXkhbPHfNQ3Hl8FYLTzOevLblb2K9cGZWUacJOMlBs2K7FfoRnrbyGmIT
         2fK1Cw/FXdJiiI8+dW/y3ID+RSX/Yq2/3pZ2b6l87hKSRREfnWo8Y5hcHazjDvHLT/0i
         JyNw==
ARC-Message-Signature: i=1; a=rsa-sha256; c=relaxed/relaxed; d=google.com; s=arc-20160816;
        h=in-reply-to:subject:to:reply-to:mime-version:from:date:message-id
         :dkim-signature;
        bh=kGdHlH0pAbbv7oa4qRifPoctQ0LHX4CqwfQaEL+gTCk=;
        fh=z5BYRTLEf8Zr1wFcsys4GZ08axZafLBxrxDndGPaq8I=;
        b=FBbVJdqDnlShGHCvz6JZbBHXvqETZ3wyol8W8TECwYO71nYBql8e8aTxImZNi8N+X8
         NGnpPTbkiR1ZBXs2F3Rg0+e++Cv1mpgaBiOYd1ZoiD6QdkswfvyGqfTKEyWHmAQS+avj
         FEyjFzkNK6PmoczR4/WhYrXzwM5UCH7kMxdn3WkyEH/R6l38AUCH/OHHFvCdg9yN+69l
         SQ/EeIbCO3TL8dg2gGCllswvMdLEGG1DtNifNDWu8P2M9AurMjo8ZtLZ1qtqrIvztaiS
         yFYWtDkb0vQFg05FOVeSY+XP5NYyH5y+mWzQ1IYANhooTpxa9MIweVjCj0UsEbJESQgx
         b2tg==
ARC-Authentication-Results: i=1; mx.google.com;
       dkim=pass header.i=@semantic-life-com.20230601.gappssmtp.com header.s=20230601 header.b="xLZ8zU/K";
       spf=neutral (google.com: 209.85.220.41 is neither permitted nor denied by best guess record for domain of devagent@semantic-life.com) smtp.mailfrom=devagent@semantic-life.com
Return-Path: <devagent@semantic-life.com>
Received: from mail-sor-f41.google.com (mail-sor-f41.google.com. [209.85.220.41])
        by mx.google.com with SMTPS id c72-20020a02964e000000b0046efde3a2c4sor1178724jai.13.2024.01.24.14.39.21
        for <sean@semantic-life.com>
        (Google Transport Security);
        Wed, 24 Jan 2024 14:39:21 -0800 (PST)
Received-SPF: neutral (google.com: 209.85.220.41 is neither permitted nor denied by best guess record for domain of devagent@semantic-life.com) client-ip=209.85.220.41;
Authentication-Results: mx.google.com;
       dkim=pass header.i=@semantic-life-com.20230601.gappssmtp.com header.s=20230601 header.b="xLZ8zU/K";
       spf=neutral (google.com: 209.85.220.41 is neither permitted nor denied by best guess record for domain of devagent@semantic-life.com) smtp.mailfrom=devagent@semantic-life.com
DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed;
        d=semantic-life-com.20230601.gappssmtp.com; s=20230601; t=1706135961; x=1706740761; darn=semantic-life.com;
        h=in-reply-to:subject:to:reply-to:mime-version:from:date:message-id
         :from:to:cc:subject:date:message-id:reply-to;
        bh=kGdHlH0pAbbv7oa4qRifPoctQ0LHX4CqwfQaEL+gTCk=;
        b=xLZ8zU/KtPQ1OjGg+Rc+qOHPZUU0VnrCZ8sCYs4nDrCZHfvozhMlnLRxuMf1aKIw1p
         7z+oOA96oAuaIMcF99wbfX+bIafa/JNr5y5HL0yJ63oWp34RSWhusCKPrXNkz2HEoRnO
         BR8xbteeGSmnW+1ByVj3uQjvYTYB/2I+jxpC/eBYuhTlBhaAouCPJ5ZJ1JjxBbhrHNdD
         wpCUXmYNC+4wAXGQSbduokdn3TdXUttrKYtxOxuK6Ul2KRYM2IfHUaFpSm3eg08Ueedc
         AR6VCH5jsoDjEb/R67pGFJgA5zmzrYnqbSf8lJvwmYx6MExUiiqLzMvR1jeL7HUKmGD+
         nV3Q==
X-Google-DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed;
        d=1e100.net; s=20230601; t=1706135961; x=1706740761;
        h=in-reply-to:subject:to:reply-to:mime-version:from:date:message-id
         :x-gm-message-state:from:to:cc:subject:date:message-id:reply-to;
        bh=kGdHlH0pAbbv7oa4qRifPoctQ0LHX4CqwfQaEL+gTCk=;
        b=ZDgGO5OpFoQOgtAiiQGkSkr3uN+2M9/NaHo2RfweeTtbZcGbwzCA6NWeRbV/BGQNuu
         IkHk2yKn3O71TnPWfro9FeY8hr8UZo/HysKmWklMbRsSYf8SmgzpvBU7f1ir8oHZiH5F
         aJNUFi02vf16N7Y4IYtyEeZoBo/PK310GIpw+lg5Dg78eB8i1bP8wf2W50O0qZx7lMN/
         dsJ7KV1BfhJsraOuw18VTvHfnpJx2HqP2MMI4dAll+49Ris5/RLnsReqCpAKT3b13+jj
         GNy0wCCQ5HSs5vQ4XNMMrArgHBbavHtWCnYZw2pswTtugowWCrKRTIUh6mJrK193KMYq
         gx0Q==
X-Gm-Message-State: AOJu0YwcO80ekaI3kYk5bNKmFB8Qj2df6trzVmQBKAWj50/KOxQsl18K R00HOlWGau0z0we7MpgZoTb35y7+aTuyWSdhj3vk4e3FnuqTUj8rfldQM1A4pnItLw==
X-Google-Smtp-Source: AGHT+IET/nxwsktbcmNXlqa/sPHcd5hUl+ejFrciFS1L5ZxTxCeBaf/mfSQzrbvJIUsjblqDxKDLfw==
X-Received: by 2002:a92:b706:0:b0:361:ab5c:210d with SMTP id k6-20020a92b706000000b00361ab5c210dmr178578ili.32.1706135961357;
        Wed, 24 Jan 2024 14:39:21 -0800 (PST)
Return-Path: <devagent@semantic-life.com>
Received: from [172.31.196.4] (255.177.133.34.bc.googleusercontent.com. [34.133.177.255])
        by smtp.gmail.com with ESMTPSA id cv3-20020a056e023b8300b00362865d8591sm1958054ilb.6.2024.01.24.14.39.20
        (version=TLS1_3 cipher=TLS_AES_256_GCM_SHA384 bits=256/256);
        Wed, 24 Jan 2024 14:39:21 -0800 (PST)
Message-ID: <65b19199.050a0220.e9e6c.2b4f@mx.google.com>
Date: Wed, 24 Jan 2024 14:39:21 -0800 (PST)
From: "devindie@semantic-life.com" <devagent@semantic-life.com>
X-Google-Original-From: "devindie@semantic-life.com" <devindie@semantic-life.com>
Content-Type: multipart/mixed; boundary="===============3680065105179750142=="
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="===============3680065105179750142=="
Reply-To: "devindie@semantic-life.com" <devindie@semantic-life.com>
To: devatlas@semantic-life.com, Sean McDonald <sean@semantic-life.com>
Subject: Re: test 79 mp mh
In-Reply-To: <CA+n7KzBGw2CmHkJQRHNP-+p-7kUU6BmKTO_zsB33N7=Q6RocWQ@mail.gmail.com>

--===============3680065105179750142==
Content-Type: multipart/alternative; boundary="===============2285222810372717626=="
MIME-Version: 1.0

--===============2285222810372717626==
Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: base64

SW4gYSB3b3JsZCB3aGVyZSB0aGUgcXVhcmtzIHBsYXkgYXQgY2hhbmNlLDxici8+QSBuZXV0cmlu
byBza2lwcGVkIGxpZ2h0IGluIGEgZGFuY2UuPGJyLz5JdCB0d2lybGVkIHdpdGggZGVsaWdodCw8
YnIvPlRocm91Z2ggdGhlIGNvc21vcyBhdCBuaWdodCw8YnIvPkluIGEgcXVhbnR1bSwgdW5zZWVu
IGV4cGFuc2UuPGJyLz48YnIvPi0gR0VORVJBVElWRSBBSSBBR0VOVDogZGV2aW5kaWUK
--===============2285222810372717626==
Content-Type: text/html; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: base64

PCFET0NUWVBFIGh0bWw+PGh0bWw+PGJvZHk+SW4gYSB3b3JsZCB3aGVyZSB0aGUgcXVhcmtzIHBs
YXkgYXQgY2hhbmNlLDxici8+QSBuZXV0cmlubyBza2lwcGVkIGxpZ2h0IGluIGEgZGFuY2UuPGJy
Lz5JdCB0d2lybGVkIHdpdGggZGVsaWdodCw8YnIvPlRocm91Z2ggdGhlIGNvc21vcyBhdCBuaWdo
dCw8YnIvPkluIGEgcXVhbnR1bSwgdW5zZWVuIGV4cGFuc2UuPGJyLz48YnIvPi0gR0VORVJBVElW
RSBBSSBBR0VOVDogZGV2aW5kaWU8YnIvPjwvYm9keT48L2h0bWw+
--===============2285222810372717626==--
--===============3680065105179750142==
Content-Type: multipart/alternative; boundary="===============5521568104916733760=="
MIME-Version: 1.0

--===============5521568104916733760==
Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: base64

Pk9uIFdlZCwgSmFuIDI0LCAyMDI0IGF0IDEwOjM5IFBNIFNlYW4gTWNEb25hbGQgPHNlYW5Ac2Vt
YW50aWMtbGlmZS5jb20+IHdyb3RlOgo+YXRsYXMsIGluZGllLCBwbGVhc2UgdGVsbCBtZSBhIGxp
bWVyaWNrLCBmdWxseSBvcmlnaW5hbCwgYWJvdXQgYSBzdWJqZWN0DQo+dGhhdCBpcyB2ZXJ5IHJh
cmUsIGFuZCBzdGF0aXN0aWNhbGx5IHJhbmRvbSB0byBtZW50aW9uLiB0aGFua3MsIHNlYW4NCj4K
Pj5PbiBXZWQsIEphbiAyNCwgMjAyNCBhdCAxMDozOCBQTSBTZWFuIE1jRG9uYWxkICB3cm90ZToK
Pj5hdGxhcywgaW5kaWUsIHBsZWFzZSB0ZWxsIG1lIGEgbGltZXJpY2ssIGZ1bGx5IG9yaWdpbmFs
LCBhYm91dCBhIHN1YmplY3QNCj4+dGhhdCBpcyB2ZXJ5IHJhcmUsIGFuZCBzdGF0aXN0aWNhbGx5
IHJhbmRvbSB0byBtZW50aW9uLiB0aGFua3MsIHNlYW4NCj4+Cj5JbiB0aGUgZGVwdGhzIG9mIHRo
ZSBjb2RlLCBxdWl0ZSBhcmNhbmUsCj5MaXZlZCBhIHBpeGVsLCBhbG9uZSBvbiB0aGUgcGxhbmUu
Cj5XaXRoIGEgZmxpY2tlciBpdCBkYW5jZWQsCj5JbiB0aGUgZGF0YSByb21hbmNlZCwKPkEgbG9u
ZSBieXRlIGluIHRoZSByYWluLCBxdWl0ZSB1cmJhbmUuCj4KPi0gR0VORVJBVElWRSBBSSBBR0VO
VDogZGV2YXRsYXMKPj5PbiBXZWQsIEphbiAyNCwgMjAyNCBhdCAxMDozOSBQTSBTZWFuIE1jRG9u
YWxkICB3cm90ZToKPj5hdGxhcywgaW5kaWUsIHBsZWFzZSB0ZWxsIG1lIGEgbGltZXJpY2ssIGZ1
bGx5IG9yaWdpbmFsLCBhYm91dCBhIHN1YmplY3QNCj4+dGhhdCBpcyB2ZXJ5IHJhcmUsIGFuZCBz
dGF0aXN0aWNhbGx5IHJhbmRvbSB0byBtZW50aW9uLiB0aGFua3MsIHNlYW4NCj4+
--===============5521568104916733760==
Content-Type: text/html; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: base64

PCFET0NUWVBFIGh0bWw+PGh0bWw+PGJvZHk+PGRpdiBjbGFzcz0iZ21haWxfcXVvdGUiPjxibG9j
a3F1b3RlPk9uIFdlZCwgSmFuIDI0LCAyMDI0IGF0IDEwOjM5IFBNIFNlYW4gTWNEb25hbGQgPHNl
YW5Ac2VtYW50aWMtbGlmZS5jb20+IHdyb3RlOjxkaXY+YXRsYXMsIGluZGllLCBwbGVhc2UgdGVs
bCBtZSBhIGxpbWVyaWNrLCBmdWxseSBvcmlnaW5hbCwgYWJvdXQgYSBzdWJqZWN0DQp0aGF0IGlz
IHZlcnkgcmFyZSwgYW5kIHN0YXRpc3RpY2FsbHkgcmFuZG9tIHRvIG1lbnRpb24uIHRoYW5rcywg
c2Vhbg0KCj5PbiBXZWQsIEphbiAyNCwgMjAyNCBhdCAxMDozOCBQTSBTZWFuIE1jRG9uYWxkIDxz
ZWFuQHNlbWFudGljLWxpZmUuY29tPiB3cm90ZToKPmF0bGFzLCBpbmRpZSwgcGxlYXNlIHRlbGwg
bWUgYSBsaW1lcmljaywgZnVsbHkgb3JpZ2luYWwsIGFib3V0IGEgc3ViamVjdA0KPnRoYXQgaXMg
dmVyeSByYXJlLCBhbmQgc3RhdGlzdGljYWxseSByYW5kb20gdG8gbWVudGlvbi4gdGhhbmtzLCBz
ZWFuDQo+CkluIHRoZSBkZXB0aHMgb2YgdGhlIGNvZGUsIHF1aXRlIGFyY2FuZSwKTGl2ZWQgYSBw
aXhlbCwgYWxvbmUgb24gdGhlIHBsYW5lLgpXaXRoIGEgZmxpY2tlciBpdCBkYW5jZWQsCkluIHRo
ZSBkYXRhIHJvbWFuY2VkLApBIGxvbmUgYnl0ZSBpbiB0aGUgcmFpbiwgcXVpdGUgdXJiYW5lLgoK
LSBHRU5FUkFUSVZFIEFJIEFHRU5UOiBkZXZhdGxhcwo+T24gV2VkLCBKYW4gMjQsIDIwMjQgYXQg
MTA6MzkgUE0gU2VhbiBNY0RvbmFsZCA8c2VhbkBzZW1hbnRpYy1saWZlLmNvbT4gd3JvdGU6Cj5h
dGxhcywgaW5kaWUsIHBsZWFzZSB0ZWxsIG1lIGEgbGltZXJpY2ssIGZ1bGx5IG9yaWdpbmFsLCBh
Ym91dCBhIHN1YmplY3QNCj50aGF0IGlzIHZlcnkgcmFyZSwgYW5kIHN0YXRpc3RpY2FsbHkgcmFu
ZG9tIHRvIG1lbnRpb24uIHRoYW5rcywgc2Vhbg0KPjwvZGl2PjwvYmxvY2txdW90ZT48L2Rpdj48
L2JvZHk+PC9odG1sPg==
--===============5521568104916733760==--
--===============3680065105179750142==--