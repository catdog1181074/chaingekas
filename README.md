# chaingekas

The goal of this blockdag-based investigation was to determine the amount of Kaspa that Chainge Finance
holds and how much it transferred to centralized exchanges for sale. This became an issue because the
Chainge Finance wrapped Kaspa (wKas) -> native Kaspa bridge has been closed since the end of 2024, which
led to a major price drop of wKas. Since soon after creating Knot.meme, Chainge closed the wKas -> Kas
bridge, claiming security concerns. Later, they changed the story to a liquidity problem, that their vaults
were blacklisted, and they needed DJ Qian to inject funds to restore their platform's operation. Chainge has
repeatedly claimed that they are planning to "inject" liquidity to allow their swap app to function properly.
Notably, many people's funds have been stuck in the bridge for months. Chainge also claimed that once the
liquidity was added, the CUSDT/Kas trading pair would re-open, and then the wKas -> native Kaspa bridge
would reopen. 

For these and more fundamental reasons, I wanted to investigate whether Chainge is likely to own the full
Kaspa reserve backing the wKas at 1:1 was still held by Chainge.

This Python code and associated data are presented to help answer that question.

The code relies on the krcbot Kaspa REST API (https://krcbot.com/api-docs) to download and track transactions
of the Chainge Finance wallet kaspa:qqwvnkp47wsj6n4hkdlgj8dsauyx0xvefunnwvvsmpq2udd0ka8ckmpuqw3k5 (https://kas.fyi/address/kaspa:qqwvnkp47wsj6n4hkdlgj8dsauyx0xvefunnwvvsmpq2udd0ka8ckmpuqw3k5) recursively,
up save the transaction output and the transactions of linked wallets, in the flow_data sub-directory. Afterwards,
analaysis of the transactions with cumulative sums are performed. I would caution people against re-running the
full download history, as this could overwhelm the krcbot API. Instead, unzip the contents of the zip files
in the flow_data directory, and continue with any analysis on the data.

The main conclusion from this investigation is that Chainge transferred hundreds of millions of Kaspa
to centralized exchanges, likely for liquidation.

