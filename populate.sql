-- Populate Nouns Table
INSERT INTO nouns (noun, meaning, example) VALUES
('communication', 'The imparting or exchanging of information or news.', 'Effective communication is key to success.'),
('strategy', 'A plan of action designed to achieve a long-term or overall aim.', 'The company developed a new marketing strategy.'),
('management', 'The process of dealing with or controlling things or people.', 'Good management is essential for a productive team.'),
('innovation', 'The action or process of innovating.', 'The company encourages innovation and creativity.'),
('customer', 'A person or organization that buys goods or services from a store or business.', 'We value our loyal customers.');

-- Populate Verbs Table
INSERT INTO verbs (verb, meaning, present_tense, past_tense, future_tense, example) VALUES
('communicate', 'Share or exchange information, news, or ideas.', 'communicate', 'communicated', 'will communicate', 'Please communicate your ideas clearly.'),
('strategize', 'Devise a strategy.', 'strategize', 'strategized', 'will strategize', 'We need to strategize our next move.'),
('manage', 'Be in charge of (a company, organization, or group of staff).', 'manage', 'managed', 'will manage', 'She can manage the project effectively.'),
('innovate', 'Make changes in something established, especially by introducing new methods, ideas, or products.', 'innovate', 'innovated', 'will innovate', 'The company continues to innovate and grow.'),
('serve', 'Perform duties or services for (another person or an organization).', 'serve', 'served', 'will serve', 'We aim to serve our customers well.');

-- Populate Adjectives Table
INSERT INTO adjectives (adjective, meaning, example) VALUES
('effective', 'Successful in producing a desired or intended result.', 'The new system is highly effective.'),
('strategic', 'Relating to the identification of long-term or overall aims and interests and the means of achieving them.', 'We made a strategic decision to expand.'),
('professional', 'Relating to or belonging to a profession.', 'He maintains a professional attitude at work.'),
('innovative', 'Featuring new methods; advanced and original.', 'The company is known for its innovative products.'),
('loyal', 'Giving or showing firm and constant support or allegiance to a person or institution.', 'Our customers are very loyal.');

-- Populate Adverbs Table
INSERT INTO adverbs (adverb, meaning, example) VALUES
('effectively', 'In a way that is successful in producing a desired or intended result.', 'The team worked together effectively.'),
('strategically', 'In a way that relates to the identification of long-term or overall aims and interests.', 'The company is strategically positioned in the market.'),
('professionally', 'In a way that relates to a profession.', 'She handled the situation professionally.'),
('innovatively', 'In a way that features new methods.', 'The problem was solved innovatively.'),
('loyally', 'In a way that shows firm and constant support.', 'He served the company loyally for many years.');

-- Populate Sentence Patterns Table
INSERT INTO sentence_patterns (pattern, structure, example) VALUES
('Subject-Verb-Object', 'S + V + O', 'The company launched a new product.'),
('Subject-Verb-Adjective', 'S + V + Adj', 'The presentation was impressive.'),
('Subject-Verb-Adverb', 'S + V + Adv', 'She speaks fluently.'),
('Subject-Verb-Prepositional Phrase', 'S + V + PP', 'He works in the marketing department.'),
('Subject-Verb-Infinitive', 'S + V + to + V', 'They decided to invest in new technology.');

-- Populate Vocabulary Table
INSERT INTO vocabulary (word, meaning, part_of_speech, example) VALUES
('synergy', 'The interaction or cooperation of two or more organizations, substances, or other agents to produce a combined effect greater than the sum of their separate effects.', 'Noun', 'The synergy between the two departments was amazing.'),
('benchmark', 'A standard or point of reference against which things may be compared or assessed.', 'Noun', 'We are benchmarking our performance against our competitors.'),
('leverage', 'Use (something) to maximum advantage.', 'Verb', 'We need to leverage our strengths.'),
('paradigm', 'A typical example or pattern of something; a model.', 'Noun', 'There has been a paradigm shift in the way we work.'),
('proactive', 'Creating or controlling a situation by causing something to happen rather than responding to it after it has happened.', 'Adjective', 'We need to be proactive in identifying potential problems.');
