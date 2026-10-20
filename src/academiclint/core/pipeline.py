"""NLP processing pipeline for AcademicLint."""

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from academiclint.core.exceptions import ModelNotFoundError, ProcessingError
from academiclint.core.result import Span

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
            ProcessingError: If spaCy fails to load for other reasons
        """
        if self._nlp is not None:
            return self._nlp

        try:
            import spacy
        except Exception as e:
            raise ProcessingError("Failed to import spaCy", original_error=e) from e

        for candidate in self._candidates:
            logger.info("Loading spaCy model: %s", candidate)
            try:
                self._nlp = spacy.load(candidate)
            except OSError:
                logger.debug("spaCy model not installed: %s", candidate)
                continue
            except Exception as e:
                logger.error("Failed to load spaCy model: %s", e)
                raise ProcessingError(
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

    def process(self, text: str) -> ProcessedDocument:
        """Process text through NLP pipeline.

        Args:
            text: The text to process

        Returns:
            ProcessedDocument with tokens, sentences, entities, etc.

        Raises:
            ModelNotFoundError: If the spaCy model is not installed
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
                for span in self._sentence_spans(doc)
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
    def _sentence_spans(doc: Any) -> list[Any]:
        """Return the doc's sentence spans, split wherever one crosses a blank line.

        The parser can run a sentence across a paragraph break (e.g. a Markdown
        heading into the body text below it). Splitting after parsing keeps the
        parser's own boundaries inside each paragraph; presetting boundaries
        before the parser instead makes the small English model mis-split the
        body sentence ("Johnson (2019) found..." -> "Johnson", "(", ...).
        """
        spans = []
        for sent in doc.sents:
            sent_text = sent.text  # Span.text is rebuilt on every access
            start = sent.start
            prev_end = None  # End of the previous non-space token, relative to sent
            for token in sent:
                if token.is_space:
                    continue
                offset = token.idx - sent.start_char
                if prev_end is not None and "\n\n" in sent_text[prev_end:offset]:
                    spans.append(doc[start : token.i])
                    start = token.i
                prev_end = offset + len(token.text)
            spans.append(doc[start : sent.end])
        return spans

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
