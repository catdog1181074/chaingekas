# chaingekas

This code uses the krcbot Kaspa REST API (https://krcbot.com/api-docs) to download and track transactions
of the Chainge Finance wallet kaspa:qqwvnkp47wsj6n4hkdlgj8dsauyx0xvefunnwvvsmpq2udd0ka8ckmpuqw3k5 (https://kas.fyi/address/kaspa:qqwvnkp47wsj6n4hkdlgj8dsauyx0xvefunnwvvsmpq2udd0ka8ckmpuqw3k5) recursively,
up to depth=2 and save the transaction output in flow_data sub-directory. Afterwards, analaysis
and visualization of the transactions with cumulative sums will be performed.

The goal of this investigation was to determine the amount of Kaspa that Chainge Finance holds and
how much it transferred to centralized exchanges for sale. This is of interest because the Chainge
wrapped Kaspa (wKas) bridge has been closed since the end of 2024, which caused a major price depeg. 

Chainge has repeatedly claimed that they are planning to "inject" liquidity to allow their swap app
to function properly. Notably, many people's funds have been stuck in the bridge for months. Chainge
also claimed that once the liquidity was added, the CUSDT/Kas trading pair would re-open, and then
the wKas -> native Kaspa bridge would reopen.
