/// <reference types="Cypress" />

class NewSolutionPage {

    getTitle() {
        return cy.get('.PageTitle')
    }
	
    getNewSolutionTitle() {
        return cy.get('[data-test="solution-name-input"]')
    }

    getSolutionName() {
        return cy.get('.el-input > [data-test="solution-name-input"]')
    }

    getAddPortfolio() {
        return cy.get('[data-test="add-portfolio-row-button"]')
    }

    getOpenSourceFrontierTech() {
        return cy.get('[data-test="solution-tech-checkbox"]')
    }

    getLearningInvestment() {
        return cy.get('[data-test="solution-learning-checkbox"]')
    }
    
    getInnovationPortfolio() {
        return cy.get('[data-test="portfolio-select-single-0"]')
    }

    getProblemStatements() {
        return cy.get('[data-test="problem-statement-0"]')
    }

    getOverrideReachValue() {
        return cy.get('[data-test="override-reach-input"]')
    }

    getAddCountry() {
        return cy.get('[data-test="add-country-button"]')
    }

    getCountry() {
        return cy.get('[data-test="country-single-select-0"]')
    }

    getPeopleReach() {
        return cy.get('[data-test="people-reached-input-0"]')
    }

    getSaveButton() {
        return cy.get('[data-test="save-solution"]')
    }

    getCancelButton() {
        return cy.get('[data-test="cancel-solution"]')
    }

    getCancelCancelButton() {
        return cy.get('.el-message-box__btns > :nth-child(1)')
    }

    getCloseButton() {
        return cy.get('.el-message-box__btns > .el-button')
    }

	typeSolutionName(name) {
        this.getSolutionName().type(name)
    }
    
    pressAddPortfolio() {
        this.getAddPortfolio().click()
    }

    setOpenSourceFrontierTech() {
        this.getOpenSourceFrontierTech().click()
    }

    setLearningInvestment() {
        this.getLearningInvestment().click()
    }

    setInnovationPortfolio(portfolio) {
        this.getInnovationPortfolio().click()
        this.getInnovationPortfolio().scrollIntoView().should('be.visible')
        cy.get('li').contains(portfolio).click()
    }

    setProblemStatements() {
        this.getProblemStatements().click()
        this.getProblemStatements().scrollIntoView().should('be.visible')
        cy.get('li').contains("1").click()
        cy.get('#general').click()
    }

    setOverrideReachValue(value) {
        this.getOverrideReachValue().click()
        this.getOverrideReachValue().type(value)
    }

    pressAddCountry() {
        this.getAddCountry().click()
    }

    setCountry(country) {
        this.getCountry().click()
        this.getCountry().scrollIntoView().should('be.visible')
        this.getCountry().type(country)
        cy.get('li').contains(country).click()
    }

    setPeopleReach(people) {
        this.getPeopleReach().click()
        this.getPeopleReach().type(people)
        cy.get('#general').click()
    }

    saveSolution() {
        this.getSaveButton().click()
    }
	
    cancelSolution() {
        this.getCancelButton().click()
    }

    cancelCancelButton() {
        this.getCancelCancelButton().click()
    }

    closeButton() {
        this.getCloseButton().click()
    }
}
export default NewSolutionPage