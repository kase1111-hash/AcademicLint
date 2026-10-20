"""NLP processing pipeline for AcademicLint."""

import logging
import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Optional

from academiclint.core.exceptions import ModelLoadError, ModelNotFoundError, ProcessingError
from academiclint.core.parser import CITATION_PLACEHOLDER
from academiclint.core.result import Span
from academiclint.utils.patterns import CITATION_PATTERNS, CITATION_REMINDERS

logger = logging.getLogger(__name__)


@dataclass
class Token:
    """A single token from the text."""

    text: str
    lemma: str
    pos: str  # Part of speech tag
    is_stop: bool
    idx: int  # Character offset in original text


@dataclass
class Sentence:
    """A sentence from the text."""

    text: str
    span: Span
    tokens: list[Token] = field(default_factory=list)


@dataclass
class Paragraph:
    """A paragraph from the text."""

    text: str
    span: Span
    sentences: list[Sentence] = field(default_factory=list)
    word_count: int = 0
    sentence_count: int = 0


@dataclass
class Entity:
    """A named entity from the text."""

    text: str
    label: str
    span: Span


@dataclass
class NounChunk:
    """A noun phrase chunk."""

    text: str
    root: str
    span: Span


@dataclass
class ProcessedDocument:
    """NLP-processed document ready for analysis."""

    text: str
    tokens: list[Token] = field(default_factory=list)
    sentences: list[Sentence] = field(default_factory=list)
    paragraphs: list[Paragraph] = field(default_factory=list)
    entities: list[Entity] = field(default_factory=list)
    noun_chunks: list[NounChunk] = field(default_factory=list)
    concept_count: int = 0
    filler_ratio: float = 0.0
    _spacy_doc: Any | None = field(default=None, repr=False)

    @property
    def spacy_doc(self) -> Any | None:
        """Access the underlying spaCy Doc, if available."""
        return self._spacy_doc

    def get_sentence_for_span(self, start: int, end: int) -> Optional["Sentence"]:
        """Find the sentence containing a character span.

        Args:
            start: Start character offset
            end: End character offset

        Returns:
            The Sentence containing the span, or None
        """
        for sent in self.sentences:
            if sent.span.start <= start and end <= sent.span.end:
                return sent
        return None


DEFAULT_MODEL = "en_core_web_lg"

# Models tried in order when no model is requested explicitly. The large model
# is preferred, but the smaller ones work for every detector (none rely on
# word vectors), so a lighter install is still usable.
FALLBACK_MODELS = ("en_core_web_lg", "en_core_web_md", "en_core_web_sm")


_CITATION = "|".join(f"(?:{pattern})" for pattern in CITATION_PATTERNS)
# Citations, or reminders of missing ones ("[citation needed]")
_CITATION_OR_REMINDER = "|".join(
    f"(?:{pattern})" for pattern in CITATION_PATTERNS + CITATION_REMINDERS
)
# A "sentence" holding nothing but those, e.g. "[12]."
_CITATION_ONLY = re.compile(rf"(?:\s*(?:{_CITATION_OR_REMINDER}))+[\s.,;:!?]*")
# A sentence opening with a bracketed citation, e.g. "[12], and others agree."
_LEADING_CITATION = re.compile(rf"(?=[\[(\u27e6])(?:{_CITATION})")
# The end of a sentence, before any citations or reminders that follow it
_SENTENCE_END = re.compile(rf"[.!?][\"'\u201d\u2019)\]]*(?:\s*(?:{_CITATION_OR_REMINDER}))*\s*$")
# The placeholder's closing bracket, which only the LaTeX parser writes
_CITATION_CLOSE = CITATION_PLACEHOLDER[-1]


class NLPPipeline:
    """Core NLP processing pipeline."""

    def __init__(self, model_name: str | None = None):
        """Initialize the NLP pipeline.

        Args:
            model_name: Name of the spaCy model to use. If None, the first
                installed model from FALLBACK_MODELS is used.
        """
        self.model_name = model_name or DEFAULT_MODEL
        self._candidates = (model_name,) if model_name else FALLBACK_MODELS
        self._nlp: Any | None = None

    def _ensure_loaded(self) -> Any:
        """Ensure the spaCy model is loaded.

        Returns:
            The loaded spaCy Language object

        Raises:
            ModelNotFoundError: If no candidate spaCy model is installed
            ModelLoadError: If spaCy or the model fails to load for other reasons
        """
        if self._nlp is not None:
            return self._nlp

        try:
            import spacy
        except Exception as e:
            raise ModelLoadError("Failed to import spaCy", original_error=e) from e

        for candidate in self._candidates:
            logger.info("Loading spaCy model: %s", candidate)
            try:
                self._nlp = spacy.load(candidate)
            except OSError:
                logger.debug("spaCy model not installed: %s", candidate)
                continue
            except Exception as e:
                logger.error("Failed to load spaCy model: %s", e)
                raise ModelLoadError(
                    f"Failed to load spaCy model '{candidate}'",
                    original_error=e,
                ) from e

            if candidate != self.model_name:
                logger.warning(
                    "spaCy model '%s' not found; using '%s' instead",
                    self.model_name,
                    candidate,
                )
            self.model_name = candidate
            logger.debug("spaCy model loaded successfully")
            return self._nlp

        logger.error("spaCy model not found: %s", self.model_name)
        raise ModelNotFoundError(self.model_name)

    def process(self, text: str, sentence_starts: Sequence[int] = ()) -> ProcessedDocument:
        """Process text through NLP pipeline.

        Args:
            text: The text to process
            sentence_starts: Offsets where a sentence starts whatever the
                parser finds (e.g. list items, from ParsedText)

        Returns:
            ProcessedDocument with tokens, sentences, entities, etc.

        Raises:
            ModelNotFoundError: If the spaCy model is not installed
            ModelLoadError: If spaCy or the model fails to load (a ProcessingError)
            ProcessingError: If NLP processing fails
        """
        nlp = self._ensure_loaded()

        try:
            doc = nlp(text)
        except MemoryError as e:
            raise ProcessingError(
                "Out of memory while processing document. "
                "Try processing a smaller document or increasing available memory."
            ) from e
        except Exception as e:
            raise ProcessingError("NLP processing failed", original_error=e) from e

        try:
            # Extract tokens
            tokens = [
                Token(
                    text=token.text,
                    lemma=token.lemma_,
                    pos=token.pos_,
                    is_stop=token.is_stop,
                    idx=token.idx,
                )
                for token in doc
            ]

            # Extract sentences, paired with their spaCy spans
            sentence_spans = [
                (sentence, span)
                for span in self._sentence_spans(doc, sentence_starts)
                if (sentence := self._build_sentence(span)) is not None
            ]
            sentences = [sentence for sentence, _ in sentence_spans]

            # Extract paragraphs (split by double newlines)
            paragraphs = self._extract_paragraphs(text, sentence_spans)

            # Extract entities
            entities = [
                Entity(
                    text=ent.text,
                    label=ent.label_,
                    span=Span(start=ent.start_char, end=ent.end_char),
                )
                for ent in doc.ents
            ]

            # Extract noun chunks
            noun_chunks = [
                NounChunk(
                    text=chunk.text,
                    root=chunk.root.text,
                    span=Span(start=chunk.start_char, end=chunk.end_char),
                )
                for chunk in doc.noun_chunks
            ]

            # Calculate concept count (unique lemmas of content words)
            content_lemmas = {
                token.lemma_
                for token in doc
                if not token.is_stop and token.pos_ in ("NOUN", "VERB", "ADJ", "ADV")
            }
            concept_count = len(content_lemmas)

            # Calculate filler ratio
            from academiclint.utils.patterns import FILLER_PHRASES

            filler_count = sum(1 for phrase in FILLER_PHRASES if phrase.lower() in text.lower())
            word_count = len([t for t in doc if not t.is_punct and not t.is_space])
            filler_ratio = filler_count / max(word_count, 1)

            return ProcessedDocument(
                text=text,
                tokens=tokens,
                sentences=sentences,
                paragraphs=paragraphs,
                entities=entities,
                noun_chunks=noun_chunks,
                concept_count=concept_count,
                filler_ratio=filler_ratio,
                _spacy_doc=doc,
            )
        except (ModelNotFoundError, ProcessingError):
            # Re-raise our own exceptions
            raise
        except Exception as e:
            raise ProcessingError("Failed to extract document features", original_error=e) from e

    @staticmethod
    def _sentence_spans(doc: Any, starts: Sequence[int] = ()) -> list[Any]:
        """Return the doc's sentence spans, split wherever one crosses a blank line.

        The parser can run a sentence across a paragraph break (e.g. a Markdown
        heading into the body text below it). Splitting after parsing keeps the
        parser's own boundaries inside each paragraph; presetting boundaries
        before the parser instead makes the small English model mis-split the
        body sentence ("Johnson (2019) found..." -> "Johnson", "(", ...).
        A sentence is also split at each of `starts`, such as list items, which
        the parser runs together when they have no full stop, and after a
        LaTeX citation that ends a sentence ("...instead [citation].\nResearch
        shows..."), which the large model can run into the next one.
        """
        spans: list[Any] = []
        pending = sorted(starts)
        next_start = 0
        before = ("", "")  # The two previous non-space tokens' text

        def add(span: Any, may_merge: bool) -> None:
            if may_merge and spans and NLPPipeline._continues_with_citation(spans[-1], span):
                spans[-1] = doc[spans[-1].start : span.end]
            else:
                spans.append(span)

        for sent in doc.sents:
            sent_text = sent.text  # Span.text is rebuilt on every access
            start = sent.start
            may_merge = True  # Whether the span from start may join the one before
            prev_end = None  # End of the previous non-space token, relative to sent
            for token in sent:
                if token.is_space:
                    continue
                forced = False
                while next_start < len(pending) and pending[next_start] <= token.idx:
                    forced = True
                    next_start += 1
                offset = token.idx - sent.start_char
                cited_end = before[0] == _CITATION_CLOSE and before[1] in (".", "!", "?")
                if prev_end is None:
                    may_merge = not forced
                elif (
                    forced
                    or (cited_end and token.text[:1].isupper())
                    or "\n\n" in sent_text[prev_end:offset]
                ):
                    add(doc[start : token.i], may_merge)
                    start = token.i
                    may_merge = not forced
                prev_end = offset + len(token.text)
                before = (before[1], token.text)
            add(doc[start : sent.end], may_merge)
        return spans

    @staticmethod
    def _continues_with_citation(prev: Any, span: Any) -> bool:
        """Whether span is a citation the parser split off the sentence before.

        The large English model ends a sentence before a bracket, so
        "... impairs recall [12]." becomes "... impairs recall" and "[12].",
        and detectors looking for a citation in the claim's sentence miss it.
        """
        doc = span.doc
        end = prev.end  # End of prev's content
        while end > prev.start and doc[end - 1].is_space:
            end -= 1
        start = span.start  # Start of span's content
        while start < span.end and doc[start].is_space:
            start += 1
        if end == prev.start or start == span.end:
            return False
        # Only the tokens at the boundary are read: prev grows with each merge
        if "\n\n" in doc[end - 1].whitespace_ + doc[end:start].text_with_ws:
            return False
        text = doc[start : span.end].text
        if _CITATION_ONLY.fullmatch(text):
            return True
        leading = _LEADING_CITATION.match(text)
        if not leading or _SENTENCE_END.search(doc[max(prev.start, end - 12) : end].text):
            return False
        if "\n" in doc[end - 1].whitespace_ + doc[end:start].text_with_ws:
            # A citation opening a line may be the subject of a new one in an
            # outline or list ("[3] reported that..."), not the claim's citation
            after = doc[start].idx + leading.end()
            for token in doc[start : span.end]:
                if token.idx >= after and not (token.is_space or token.is_punct):
                    return token.pos_ not in ("VERB", "AUX")
        return True

    @staticmethod
    def _build_sentence(sent: Any) -> Sentence | None:
        """Convert a spaCy sentence span into a Sentence.

        The text and span are trimmed to the sentence's content: spaCy folds
        leading whitespace (e.g. a document's opening newline) into the first
        sentence, which would break detectors that anchor patterns at the
        start of the sentence and push flag positions onto the wrong line.

        Returns:
            The Sentence, or None if the span is whitespace only
        """
        stripped = sent.text.strip()
        if not stripped:
            return None
        start = sent.start_char + len(sent.text) - len(sent.text.lstrip())
        tokens = [
            Token(
                text=token.text,
                lemma=token.lemma_,
                pos=token.pos_,
                is_stop=token.is_stop,
                idx=token.idx,
            )
            for token in sent
        ]
        return Sentence(
            text=stripped,
            span=Span(start=start, end=start + len(stripped)),
            tokens=tokens,
        )

    def _extract_paragraphs(
        self, text: str, sentence_spans: list[tuple[Sentence, Any]]
    ) -> list[Paragraph]:
        """Extract paragraphs from text.

        This method reuses the already-processed spaCy doc to avoid
        re-processing each paragraph through the NLP pipeline.

        Args:
            text: Original text
            sentence_spans: Sentences paired with their spaCy spans

        Returns:
            List of Paragraph objects

        Raises:
            ProcessingError: If paragraph extraction fails
        """
        try:
            paragraphs = []
            para_texts = text.split("\n\n")

            current_pos = 0
            for raw_para in para_texts:
                para_text = raw_para.strip()
                if not para_text:
                    continue

                # Find the start position in original text
                start = text.find(para_text, current_pos)
                if start == -1:
                    start = current_pos
                end = start + len(para_text)
                current_pos = end

                # Find sentences that fall within this paragraph's span
                # by checking if sentence start is within paragraph bounds
                para_sentences = []
                word_count = 0

                for sentence, sent in sentence_spans:
                    if start <= sentence.span.start < end:
                        para_sentences.append(sentence)
                        # Count words in this sentence (non-punctuation, non-space)
                        word_count += len([t for t in sent if not t.is_punct and not t.is_space])

                paragraphs.append(
                    Paragraph(
                        text=para_text,
                        span=Span(start=start, end=end),
                        sentences=para_sentences,
                        word_count=word_count,
                        sentence_count=len(para_sentences),
                    )
                )

            return paragraphs
        except Exception as e:
            raise ProcessingError("Failed to extract paragraphs", original_error=e) from e
