# NeithCore

NeithCore is a Kyber-round-1-style lattice/NTT engine. It is designed to accelerate polynomial arithmetic operations used in lattice-based cryptography, primarily focusing on the Number Theoretic Transform (NTT), polynomial multiplication, component-wise operations, and coefficient compression/decompression.

## Core Characteristics

- **Constant-Time Execution by Construction:**
  A critical security property of NeithCore is that all datapaths are purely fixed-latency by construction. There are **no data-dependent branches, early-outs, or variable-latency operations**.
  - All arithmetic operations (e.g. Barrett reduction, butterfly) take a deterministic number of cycles regardless of the input data values.
  - This property is mandatory for lattice engines to avoid timing side-channels that could leak sensitive keys or polynomials.

## Scope & Functionality

NeithCore provides the following accelerated operations:
- **NTT / INTT:** Forward and Inverse Number Theoretic Transforms using gentleman-sande and cooley-tukey butterfly networks.
- **Polynomial Multiplication:** Schoolbook and pointwise polynomial multiplication.
- **Polynomial Addition/Subtraction:** Component-wise modular arithmetic on polynomials.
- **Compression / Decompression:** Efficient dropping and restoring of low-order bits (`Compress_q` and `Decompress_q`).
- **Message Codecs:** Encoding byte streams into polynomial coefficients and decoding back.
- **Noise Sampling:** CBD (Centered Binomial Distribution) noise generation from uniform random seeds.

The design relies on compile-time constants (such as the Kyber modulus `Q = 7681`) to simplify hardware and optimize area (e.g., constant-Q division mapping to reciprocal-multiply networks in Yosys).
