# vivino-scanner

This is a simple script that scans the Vivino website for the best price of a wine. It uses the Vivino API to get the wine details and then uses the Wine-Searcher API to get the best price. The hardest part is scanning the pdfs.

*PLAN:*
- create a script that does an initial scan of the pdfs to speed up the process of creating training data.
- once I have ~50 pdfs, I will fine-tune the model on the training data using few shot learning and [unisloth](https://colab.research.google.com/drive/1a_T0CEfC7BfudVNLVTKIwZ8pKhFqA-Ks) to create a model that specializes in scanning wine pdfs.
- Then I can make the front end.