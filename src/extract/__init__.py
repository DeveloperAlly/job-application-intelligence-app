"""S-02 advertisement field extraction.

Produces the seven fields R-120 names from the advertisement source text, with
every value anchored to a span of that text. A value that cannot be anchored is
the literal unknown token, per R-121.

The source text is treated as untrusted data throughout. It is never an
instruction to this program or to anything this program calls. See injection.py.
"""
