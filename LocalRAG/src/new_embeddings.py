from langchain.docstore.document import Document

from .embed import load_and_split_data
from .get_vector_db import getDatabases
from .utils.llm_get_tags import llmGetTags
from .utils.llm_summarize_text import llmSummarizeText, llmCheckSummarizeText
from .utils.save_file import saveFile
import re

def doEmbeddings(file, model, pdfReader, namespace):

    file_path = saveFile(file, [model, namespace])
    chunks = load_and_split_data(file_path, pdfReader)

    if isinstance(chunks, str):
        return chunks
    if not chunks and chunks != False:
        print("No chunks found")
        return False

    if chunks != False:
        db = getDatabases(model, namespace)

        for i, chunk in enumerate(chunks):
            print('---', i, ' of ', len(chunks), '---')
            shouldBreak = False
            count = 0
            while not shouldBreak:
                count = count + 1
                chapters, summary = llmSummarizeText(chunk.page_content)

                isOk = llmCheckSummarizeText(chapters, summary)
                # print('xx', count, isOk)
                if isOk == 'yes' or count == 3:
                    chapterTags = llmGetTags(chapters)
                    summarizeTags = llmGetTags(summary)
                    #print('**', chapters, '\n**', summary, '\n**',summarizeTags,'\n**', chapterTags, "*\n\n")

                    shouldBreak = True

                    chaptersSplit = chapters.split('\n')

                    chapterChunks = []
                    for chapter in chaptersSplit:
                        #print("====>", chapter)
                        found = re.match(r"((\s?)+?\d+\. Chunk \(?\d+ of \d+\)?:?\s+?)", chapter) #delete chunks
                        if found is None:
                            #print("==<0")
                            found = re.match(r"((\s?)+?\d+\. Chunk \(?\d+ of \d+\)?=?>?\s+?)", chapter)  # delete chunks
                        if found is None:
                            #print("==<1")
                            found = re.match(r"((\s?)+?Chunk \(?\d+ of \d+\)?:?\s+?)", chapter)  # delete chunks
                        if found is None:
                            #print("==<1b")
                            found = re.match(r"((\s?)+?Chunk \d+:?\s+?)", chapter)  # delete chunks
                        if found is None:
                            #print("===<2")
                            found = re.match(r"((\s?)+?\d+\. Chunk \d+:?\s+)", chapter)
                        if found is None:
                            #print("===<3")
                            found = re.match(r"((\s?)+?\d+\.\s+)", chapter)

                        if found is None:
                            #print("===<4")
                            if len(chapterChunks) == 0: continue # ignore first summary stupid idea of llm after changes?
                            if chapterChunks[len(chapterChunks) -1]['body'] ==  '':
                                chapterChunks[len(chapterChunks) -1]['body'] = chapterChunks[len(chapterChunks) -1]['body'] + chapter.replace('SUMMARY:', '').strip().lstrip("- ")
                            else:
                                chapterChunks[len(chapterChunks) - 1]['body'] = chapterChunks[len(chapterChunks) - 1]['body'] + chapter.strip()
                        else:
                            chapterChunks.append({"title": chapter.replace(found.group(), '').strip(), 'body': ''})

                    found = re.match(r"((\s?)+Final Summary:\s+?)", summary)
                    if found is None: pass
                    else:
                        summary = summary.replace(found.group(), '').strip()

                    documents = []
                    for i, chapter in enumerate(chapterChunks):
                        try:
                            chunkTags = chapterTags[i]['tags']
                            chunkTagsString = ",".join(chunkTags)
                            title = chapter['title']
                            chunkSummary = chapter['body']

                            #print(chunk.page_content, len(chunk.page_content))
                            document = Document(page_content=chunk.page_content, metadata={'title': title,'summary': chunkSummary, 'tags': chunkTagsString, 'file': file_path, 'finalSummary': summary})
                            documents.append(document)
                        except Exception as e:
                            print('=>>>>', i, chapter, chapterTags, chapterChunks)
                            print(chapters, summary, summarizeTags, "2\n\n")
                            print(e)
                    db.add_documents(documents)

                        # this cursed code, EXECUTED PROMPT FOR EMBEDDING ___FOR EACH WORD IN GIVEN STRING___
                        # db.add_texts(chunk.page_content, metadata=[{'title': title},{'summary': chunkSummary}, {'tags': chunkTags}, {'file': file_path}, {'finalSummary': summary}],             embedding=FastEmbedEmbeddings(),)
                        # and this works correctly - WTF
                        # db.add_texts([chunk.page_content], metadata=[{'title': title},{'summary': chunkSummary}, {'tags': chunkTags}, {'file': file_path}, {'finalSummary': summary}],             embedding=FastEmbedEmbeddings(),)
    return True

