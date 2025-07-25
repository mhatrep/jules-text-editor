-- Nouns Table: Stores nouns with their meanings and examples.
CREATE TABLE nouns (
    id INTEGER PRIMARY KEY,
    noun TEXT NOT NULL,
    meaning TEXT NOT NULL,
    example TEXT
);

-- Verbs Table: Stores verbs with their meanings, tenses, and examples.
CREATE TABLE verbs (
    id INTEGER PRIMARY KEY,
    verb TEXT NOT NULL,
    meaning TEXT NOT NULL,
    present_tense TEXT,
    past_tense TEXT,
    future_tense TEXT,
    example TEXT
);

-- Adjectives Table: Stores adjectives with their meanings and examples.
CREATE TABLE adjectives (
    id INTEGER PRIMARY KEY,
    adjective TEXT NOT NULL,
    meaning TEXT NOT NULL,
    example TEXT
);

-- Adverbs Table: Stores adverbs with their meanings and examples.
CREATE TABLE adverbs (
    id INTEGER PRIMARY KEY,
    adverb TEXT NOT NULL,
    meaning TEXT NOT NULL,
    example TEXT
);

-- Sentence Patterns Table: Stores common sentence patterns with their structures and examples.
CREATE TABLE sentence_patterns (
    id INTEGER PRIMARY KEY,
    pattern TEXT NOT NULL,
    structure TEXT NOT NULL,
    example TEXT
);

-- Vocabulary Table: A general table for other vocabulary words that don't fit into the above categories.
CREATE TABLE vocabulary (
    id INTEGER PRIMARY KEY,
    word TEXT NOT NULL,
    meaning TEXT NOT NULL,
    part_of_speech TEXT,
    example TEXT
);
