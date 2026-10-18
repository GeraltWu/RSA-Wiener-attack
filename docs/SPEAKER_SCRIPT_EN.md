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

## Slide 5: Live Demo (about 3 minutes)

Now, we will demonstrate the complete attack process. All RSA parameters and attack
results shown on the screen were generated and calculated during this run.

First, we construct a weak RSA key with a two-thousand-and-forty-eight-bit modulus. As
we can see, we intentionally choose a small d. This d is about seventy-five
percent of the Wiener bound, so this key satisfies the
condition for Wiener’s attack. 

Next, we use this RSA key to encrypt a test message. 

Now, we move to the attacker’s view. The attacker knows only the public e and n.
We first use these two values to calculate the continued fraction of e over n and obtain
this coefficient list. 

We then try the convergents one by one and look for a candidate d that can recover the
other RSA parameters. When the program reaches the convergent shown here, its
denominator, which is our candidate d, passes all the validation checks.

First, after checking this we can make sure our candidate phi is integer. Once phi is known, we can calculate p plus q. Together with p times q equals n, then we can construct the quadratic equation we have mentioned. Then we get the two roots of the equation, which is p and q.
it recoverd all the rsa parameters

Finally, we use the recovered d to decrypt the earlier ciphertext and successfully get
the original test message. Now the weak RSA key has been broken.

We also construct a normal RSA key as a control. It uses the same large modulus size and follows the normal process, we use this value as e, which is lot of instructions and our lecture slides recomanded.
Here, d is very large and far beyond the Wiener bound.

We run exactly the same Wiener attack again. This continued fraction contains only the
number of coefficients shown here, which is expected because e is only seventeen bits.
The attack function finally returns None, meaning that it found no candidate d that
passed all the checks in this run.

Next, we look at the results from repeated experiments with different parameters.

---

## Slide 6: Experimental Results (about 1 minute)

Here, we have three repeated experiments, with thirty trials in each parameter group.

The left chart fixes the modulus size at two thousand and forty-eight bits and changes
the ratio between d and the Wiener threshold. Every trial succeeded from 0.25 to 1.5.
From 2.0 onward, the overall success rate decreased

The upper-right chart fixes d over T at 0.75 and changes the modulus size. All four
groups of weak keys were recovered. The runtime increased with the modulus size, but
even the two-thousand-and-forty-eight-bit weak keys were still recovered in milliseconds.

The lower-right result directly compares weak and normal RSA at 2048 bits. All thirty
weak keys were recovered, while none of the thirty normal keys were recovered. 

Finally, we list the core functions that we declare as our own implementation.

---

## Slide 7: Self-Implemented Code (about 20 seconds)

These are the core functions that we declare as our own implementation. They include
the normal and weak RSA parameter-generation workflows, the Wiener-bound calculations,
the continued-fraction and convergent algorithms, and the complete candidate-testing
and attack procedure. Thank you.

