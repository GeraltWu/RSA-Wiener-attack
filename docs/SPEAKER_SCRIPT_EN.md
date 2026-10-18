# RSA Wiener Attack Presentation Script (English)

Estimated total time: approximately 7 minutes 20 seconds.

---

## Slide 1: Title (about 15 seconds)

Hello everyone. Our project studies Wiener’s small-private-exponent attack against
RSA. Our main question is: even when the RSA modulus is 2048 bits long, can an
attacker recover the private exponent using only the public values e and n if d is
chosen too small?

We will first review where this vulnerability comes from and which mathematical
relationship Wiener’s attack exploits.

---

## Slide 2: Small Private Exponent Vulnerability and Wiener Attack (about 40 seconds)

Here is a short review of Wiener’s attack. When d satisfies the condition shown on the
slide, k over d becomes very close to e over n.

More specifically, we write e over n in the continued-fraction form shown on the
right and truncate it successively. This gives the convergents shown below, and each
denominator becomes a candidate private exponent.

The convergents provide only a small set of candidates, so we do not need to enumerate
every possible d starting from one. This slide explains where the candidates come
from; the full verification procedure appears in the later attack flowchart.

To evaluate the vulnerability, we generate both normal RSA keys and valid RSA keys
whose private exponent is intentionally small.

---

## Slide 3: Normal RSA vs Weak RSA Key Construction (about 55 seconds)

The first half of both procedures is identical. Both generate similarly sized primes
p and q and then calculate n and phi.

The left side shows normal RSA. It first selects the common public exponent 65537 and
then calculates the corresponding private exponent d.

The right side shows our weak-key construction. We first calculate the Wiener
threshold from n and then choose a small d using the requested ratio. Because d must
be coprime with phi, the program searches near the target for a suitable odd value and
then calculates e in the reverse direction.

The weak key is therefore not an arbitrary collection of numbers. It still satisfies
the RSA parameter relationships, but d has intentionally been placed in the range
targeted by Wiener’s attack.

After key generation, the attack does not read p, q, d, or phi from the generator. It
receives only the public e and n.

---

## Slide 4: Wiener Attack Candidate Recovery (about 1 minute 10 seconds)

The attack receives only the public values e and n. It first calculates the continued
fraction of e over n and treats each convergent as a candidate k and d.

If k divides e times d minus one, the program can derive an integer candidate for phi.

It then uses phi to calculate p plus q. Since the product of p and q is n, they must be
the two roots of the quadratic equation shown on the slide.

For a correct candidate, the discriminant equals the square of p minus q, so it must
be non-negative and a perfect square. The program then uses the quadratic formula to
recover candidate values for p and q.

Finally, the program verifies that p times q equals n, phi equals the product of p
minus one and q minus one, and e times d modulo phi equals one. It returns d, p, and q
only when every check passes. Otherwise, it continues with the next convergent.

We will now generate two 2048-bit RSA keys live and test both keys through exactly the
same attack interface.

---

## Slide 5: Live Demo (about 2 minutes 30 seconds)

### 1. Data source

Both keys were randomly generated during this run, and both moduli are actually 2048
bits long. The first key intentionally uses a small d, while the second uses the normal
construction with e equal to 65537.

### 2. Weak-key condition

The weak key uses a d approximately 75 percent of the Wiener threshold, so it is
inside the classical boundary used in our project. The generator keeps d, p, q, and
phi only for final verification; these values are not passed to the attack.

### 3. Continued fraction and successful candidate

The program calculates the continued fraction of e over n and examines its
convergents. These lines show the number of the successful candidate, its k, and its
candidate d. We do not need to read every continued-fraction coefficient.

### 4. Recovery process

This output follows the algorithm shown on the previous slide. The program first
obtains phi from the candidate k and d, calculates p plus q, constructs the quadratic
equation, checks the discriminant, and finally recovers p and q.

### 5. Successful verification

The recovered phi, p, q, and d all match the private reference values retained by the
live generator. The recovered d also decrypts the test message correctly.

### 6. Normal RSA control

The normal key also has a 2048-bit modulus, but its d is far beyond the Wiener
boundary. The identical attack returns None in this run. This is not a complete proof
of RSA security, but it demonstrates that the earlier recovery depended on the small-d
weakness rather than applying to every RSA key.

A single live run demonstrates only one pair of keys. We therefore generated multiple
random keys to measure success rates and attack time.

---

## Slide 6: Experimental Results (about 1 minute 30 seconds)

The left experiment fixes the modulus size at 2048 bits and changes d over T, with 30
trials in each group. Every key was recovered in the groups from 0.25 through 1.5.
Starting at 2.0, the overall success rate decreased, although some samples beyond the
boundary were still recovered. The boundary should therefore not be interpreted as a
point beyond which every attack immediately fails.

The upper-right experiment fixes d over T at 0.75 and changes the modulus size. All 30
keys were recovered in each of the 256-, 512-, 1024-, and 2048-bit groups. The median
attack time increased from 0.179 milliseconds to 6.425 milliseconds. The runtime
increased with the modulus size, but the 2048-bit weak keys were still recovered in
milliseconds.

The lower-right table shows the 2048-bit control experiment. All 30 weak keys were
recovered, while none of the 30 normal keys were recovered. In this experiment, using
a larger modulus did not prevent the attack when d remained too small.

These are course-scale randomized experiments. Returning None only means that Wiener’s
attack did not succeed on these samples; it is not a complete security proof against
all possible attacks on RSA.

Finally, we list the core functions that we declare as our own implementation.

---

## Slide 7: Self-Implemented Code (about 20 seconds)

These are the core functions that we declare as our own implementation. They include
the normal and weak RSA parameter-generation workflows, the Wiener-bound calculations,
the continued-fraction and convergent algorithms, and the complete candidate-testing
and attack procedure. Thank you.

