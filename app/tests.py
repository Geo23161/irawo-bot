from django.test import TestCase

# Create your tests here.

PHYS_QUEST = [
    {
        'question' : "Description du produit",
        "title" : "Entrez tout ce que vous avez comme description sur le produit",
        "typ" : "text",
        "answers" : ""
    },
    {
        'question' : "Où, Comment et Quand pouvez-vous livrer le produit?",
        'title' : "Veuillez renseigner toutes les informations liées à la livraison du produit",
        "typ" : "text",
        "answers" : ""
    },
    {
        "question" : "Prix, Promotion et reduction",
        "title" : "Entrez le prix du produit et toutes les autres offres que vous proposez au clients qui achetent",
        "typ" : "text",
        "answers" : ""
    },
    {
        "question" : "Comment utiliser le produit?",
        "title" : "Si c'est déjà dans la description, entrez le chiffre 0 et continuer",
        "typ" : "text",
        "answers" : ""
    }
]

NUM_QUEST = [
    {
        'question' : "Description du produit",
        "title" : "Entrez tout ce que vous avez comme description sur le produit",
        "typ" : "text",
        "answers" : ""
    },
    {
        "question" : "Prix, Promotion et reduction",
        "title" : "Entrez le prix du produit et toutes les autres offres que vous proposez au clients qui achetent",
        "typ" : "text",
        "answers" : ""
    },
    {
        "question" : "Comment utiliser le produit?",
        "title" : "Si c'est déjà dans la description, entrez le chiffre 0 et continuer",
        "typ" : "text",
        "answers" : ""
    }
]

COMMAND_LIVRAISON = {
    "question" : "Qu'est ce que je fais pour obtenir le produit la maintenant, si je veux acheter?",
    "title" : "",
    "typ" : "text",
    "answers" : "Pour recevoir le produit, vous devez cliquez sur le bouton Commander juste en haut de la discussion et laisser vos coordonnées en remplissant le formulaire qui apparaît. Notre livreur va vous contacter aussitôt que possible pour vous livrer le produit."
}

COMMAND_EVENT = {
    "question" : "Qu'est ce que je fais pour obtenir le produit la maintenant, si je suis interessé?",
    "title" : "",
    "typ" : "text",
    "answers" : "Pour obtenir le produit, vous devez cliquez sur le bouton Continuer juste en haut de la discussion. Vous serez redirigé vers la page de paiement ou vous pouvez payer et obtenir le produit."
}

COMMAND_PAIEMENT = {
    "question" : "Qu'est ce que je fais pour m'inscrire la maintenant, si je suis interessé?",
    "title" : "",
    "typ" : "text",
    "answers" : "Pour vous inscrire, vous devez cliquez sur le bouton Continuer juste en haut de la discussion. Et remplissez le formulaire et soumettez."
}
