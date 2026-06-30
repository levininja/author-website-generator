# Author Website Generator — Product Decisions

Related documents: [README](README.md) · [Product spec](SPEC.md) · [Feature list](FEATURES.md) · [Provisioning pipeline](PIPELINE.md)

This file records the product's strategic decisions and their primary rationale.

---

## Users can generate a website before creating an account

AWG landing pages, onboarding, and website generation are available without an account or payment. This lets users experience the product's core value with minimal initial friction; account creation can happen afterward.

---

## Users get a 7-day free trial

The trial starts when the site is created, and payment is required after 7 days to keep it live. This lets authors evaluate and share the finished site before committing to payment.

---

## Standard sites share a server; ecommerce sites do not

Standard author websites are separate WordPress applications on one shared Cloudways server. Each ecommerce website gets a dedicated server because its resource usage and security exposure are less predictable.

---

## The ecommerce demo uses ecommerce infrastructure

The ecommerce demo is hosted on its own dedicated server with type `ecommerce`. Matching production infrastructure makes its provisioning tests representative.

---

## v1 supports new WordPress sites only

v1 does not import content or configuration from existing WordPress, Divi, or hosting setups. Limiting the initial scope avoids the variability of migrations.

---

## There are no growth deadlines

The goal is to earn the first dollar as soon as practical without setting revenue deadlines. This avoids premature scaling based on assumed growth.

---

## Ecommerce is excluded from v1

Ecommerce support is deferred until the standard-site pipeline is stable because it adds security, liability, and infrastructure complexity.

---

## AWG does not store or process credit card details

Stripe collects and retains payment details; AWG stores only the references and customer data required to provide the service. This reduces security exposure and compliance scope.

---

## Initial marketing targets existing WordPress users

Initial marketing targets authors who are already comfortable with WordPress because they face less adoption friction.

---

## Marketing uses testimonials and live examples

The marketing site uses testimonials and links to live examples to establish trust in a new service.

---

## AWG uses Django 5.2 LTS

Django provides a long-term-supported Python foundation with built-in data, authentication, security, migration, and testing capabilities.

---

## User accounts use a custom model with UUID primary keys

AWG uses `accounts.User` with a random UUID v4 primary key. Defining the custom model before other models reference users avoids a difficult later migration, while UUIDs provide stable, non-sequential identifiers without embedding PII.

---

## The onboarding and generation application uses React

AWG uses React for a two-part frontend application backed by Django:

1. Onboard the user by collecting the information needed to build an author website.
2. Generate the website from the submitted information and communicate the result.

React is appropriate for the shared state and interactive workflow across these stages, while Django remains responsible for backend validation, persistence, and generation.

Whether onboarding uses a wizard or one complete form is not yet decided. A possible third React stage for viewing the generated website is also deferred; the preview may instead be rendered or served outside the React application.
