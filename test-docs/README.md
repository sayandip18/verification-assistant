# Test documents

Sample sale deeds (Dalil) and Record of Rights (Porcha) for trying the app from the UI. They are plain `.txt` files, so they work without Tesseract installed.

Each scenario is a pair with the same file name in `dalil/` and `porcha/`.

| Scenario | Transferor (Dalil) | Recorded owner (Porcha) | Expected AI chain check |
| --- | --- | --- | --- |
| `a-inheritance-gap` | Aparna Das | Bimal Das | **Link documents needed** (amber). Same surname, different given name: asks for a link deed or legal heir certificate. |
| `b-spelling-variant` | শ্রী বিমল কুমার দাস | Bimal Das | **Likely same person** (green). Bengali script, honorific and middle name only. The rule-based check would wrongly flag this one. |
| `c-clear-mismatch` | Hasan Ali | Gopal Banerjee | **Ownership mismatch** (red). No visible link, and khajna is due since 2022. |

## How to use

1. Sign in at http://localhost:3000 with `officer@bllro.local` / `changeme`.
2. Open **New intake**. Upload `dalil/<scenario>.txt` as the Sale deed and `porcha/<scenario>.txt` as the Porcha. The form fields fill in from the files. Save.
3. On the application page, click **Run AI chain check** and compare the verdict with the table above.
4. Move the file through **Send to field verification** → **Mark ready for decision**. Then try:
   - **Return to applicant** (scenario A): draft the notice with AI in বাংলা, edit it, and confirm.
   - **Approve mutation** (scenario B): goes through without a warning.
   - **Approve mutation** (scenario C): asks you to confirm, because the check flagged it.
5. Check **History** on each file: status changes, field edits, AI runs and the notice that was sent.

AI verdicts come from a language model, so wording varies between runs. The verdict category should match the table.
