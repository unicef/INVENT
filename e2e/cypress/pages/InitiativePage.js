/// <reference types="Cypress" />

class InitiativePage {

    getGeneralCard() {
        return cy.get('[id="general"]')
    }
	
    // What is the name of the initiative? ||| Required to save draft + Required to publish
    getInitiativeName() {
        return cy.get('input[data-as-name="Name"]')
    }
	
    // Which UNICEF Office supports the initiative? ||| Required to save draft + Required to publish
    getUnicefOffice() {
        return cy.get('input[placeholder="UNICEF office"]')
    }
	
    // Please provide a brief overview of the initiative. ||| Required to publish
    getIniativeOverview() {
        return cy.get('textarea[data-vv-name="overview"]')
    }
	
    // Focal Point Label
    getFocalPointLabel() {
        return cy.get(':nth-child(9) > .el-form-item__label')
    }

    // Focal Point ||| Required to publish
    getFocalPointField() {
        return cy.get('[data-vv-name="contact_email"]')
    }

    // Focal Point Hint
    getFocalPointHint() {
        return cy.get(':nth-child(9) > .el-form-item__content > .Hint')
    }

    // Team Members Label
    getTeamMembersLabel() {
        return cy.get('.TeamArea > [draftrule="[object Object]"] > .el-form-item__label > :nth-child(1)')
    }

    // Team Members field
    getTeamMembersField() {
        return cy.get('[data-vv-name="team"]')
    }

    // Team Members Hint
    getTeamMembersHint() {
        return cy.get('.TeamArea > [draftrule="[object Object]"] > .el-form-item__content > .Hint')
    }
	
    // Members Dropdown menu
    getMembersDropdown() {
        return cy.get('.TeamSelectorDropdown')
    }

    // Receive Updates Label
    getReceiveUpdatesLabel() {
        return cy.get('[value=""] > .el-form-item__label > :nth-child(1)')
    }

    // Receive Updates field
    getReceiveUpdatesField() {
        return cy.get('[data-vv-name="viewers"]')
    }

    // Receive Updates Hint
    getReceiveUpdatesHint() {
        return cy.get('[value=""] > .el-form-item__content > .Hint')
    }

    // Who else should be able to modify this initiative's entry? ||| Required to save draft + Required to publish
    getModifyInitiative() {
        return cy.get('[data-vv-name="team"]').click()
    }
	
	// Please select the sector(s) the initiative serves. ||| Required to publish
    getLeadSectorInitiative() {
        return cy.get('div[data-vv-name="unicef_leading_sector"]')
    }

    getSupportingSectorsInitiative() {
        return cy.get('div[data-vv-name="unicef_supporting_sectors"]')
    }
	
	
	// Which Goal Area does the initiative focus on? ||| Required to publish
    getGoalArea() {
        return cy.get('[data-vv-name="goal_area"]').click()
    }
	
	// Please select the date the initiative was started. ||| Required to publish
    getStartDate() {
        return cy.get('[data-vv-name="start_date"]').click()
    }
	
	// Please select the partner type. ||| Required to publish
    getPartnerType() {
        return cy.get('div[data-vv-as="Partner Type"]')
    }
	
	// Please provide the name of your partner. ||| Required to save draft + Required to publish
    getPartnerName() {
        return cy.get('input[data-vv-as="Partner Name"]')
    }
	
    // Select all the software platform(s) used in the deployment of the initiative. ||| Required to publish
    getSoftwarePLatform(){
        return cy.get('[data-vv-name="platforms"]')
    }
	
	// Pop up Window
	getPopWindow(){
        return cy.get('[role="dialog"]')
    }
    
    // Save Draft Button on Page
	getSaveDraftButton() {
        return cy.get('[class="el-button el-button--primary el-button--medium SaveDraft NewProject"]')
    }
	
    // Draft Button on Switch View
    getViewDraftButton() {
        return cy.get('.DraftButton')
    }

    // Publish Button on Page
    getPublishButton() {
		return cy.get('.NavigationActions > .el-button--primary')
	}
	
    // Publish Button on Switch View
    getViewPublishButton() {
        return cy.get('.PublishedButton')
    }

    // Publish as latest
    getPublishAsLatestButton() {
        return cy.get('.NavigationActions > .el-tooltip')
    }

    // Unpublish Button
    getUnpublishButton() {
        return cy.get('.button--danger')
    }

    // Go to Dashboard
    getGoToDashboard() {
        return cy.get('.GoToDashboard').contains('Go to Dashboard')
    }

	// Close Button
	getCloseButton(){
        return cy.contains('Close')
    }

    // Cancel Button on Page
    getCancelButton() {
        return cy.get('.NavigationActions > .CancelButton')
    }
	
    // Verify Draft Label
    getDraftLabel() {
        return cy.get('[class="DraftLabel"]')
    }

    // Verify Published Label
    getPublishLabel() {
        return cy.get('.PublishedLabel')
    }

    // Verify Focal Point Field is Empty
    emptyFocalPointField() {
        this.getFocalPointField().should('have.value', '')
    }
        getDropDownList() {
        return  cy.get('ul[class="el-scrollbar__view el-select-dropdown__list"]')
    }


    // Verify Focal Point Field is Empty 
    emptyReceiveUpdatesField() {
        this.getReceiveUpdatesField().should('have.value', '')
    }

	typeInitiativeName(name) {
        this.getInitiativeName().type(name)
    }
    
	typeInitiativeOverview(overview) {
        this.getIniativeOverview().type(overview)
    }
	
    typeFocalPointField(focalpointmember) {
        this.getFocalPointField().type(focalpointmember)
        cy.contains(focalpointmember)
        this.getMembersDropdown().click()
    }

    typeTeamMembersField(teammebername) {
        this.getTeamMembersField().type(teammebername)
        cy.contains(teammebername)
        this.getMembersDropdown().click()
    }
	
    typeModifyInitiative(email)  {
        this.getModifyInitiative().click({force:true})
        this.getModifyInitiative().type(email).click({force:true})
        this.getModifyInitiative().scrollIntoView()
        cy.contains(email).click({force:true})
    }
	
    typePartnerName(name) {
        this.getPartnerName().type(name)
    }
	
	selectUnicefOffice(office) {      
        this.getUnicefOffice().click()
        this.getUnicefOffice().type(office)
        this.getUnicefOffice().scrollIntoView()
        cy.contains(office).click({force:true})
    }
	
	selectLeadSectorInitiative(sector) {
        this.getLeadSectorInitiative().click()
        this.getDropDownList().eq(19).contains(sector).click({force:true})
        this.getLeadSectorInitiative().dblclick()
    }

    selectSupportingSectorsInitiative(sector) {
        this.getSupportingSectorsInitiative().click()
        this.getDropDownList().eq(19).contains(sector).click({force:true})
        this.getSupportingSectorsInitiative().dblclick()
    }
	
	selectGoalArea(goalarea) {
       this.getGoalArea().click()
       cy.contains(goalarea).click({force:true})
   }
	
	selectStartDate(startdate) {
       this.getStartDate().click()
       this.getStartDate().type(startdate).type('{enter}')
	}
	
	selectPartnerType(partner) {
        this.getPartnerType().click({force:true})
        this.getPartnerType().type(partner)
        this.getPartnerType().scrollIntoView()
        cy.contains(partner).click()
    }
	
	selectSoftwarePLatform(software) {
        this.getSoftwarePLatform().click({force:true})
        this.getSoftwarePLatform().type(software)
        this.getSoftwarePLatform().scrollIntoView()
        cy.get('li').last().click({force: true})
        this.getSoftwarePLatform().click()
    }
	
    saveDraft() {
        this.getSaveDraftButton().click()
    }
	
    publishInitiative() {
        this.getPublishButton().click()
    }
	
    cancelInitiative() {
        this.getCancelButton().click({force:true})
    }
	
    closePopUpWindow(){
        this.getCloseButton().click()
    }

}
export default InitiativePage