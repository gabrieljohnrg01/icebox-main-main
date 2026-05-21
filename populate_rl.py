import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from incubator.models import RLTemplate, RLTemplateLevel

RL_DATA = {
    "TRL": {
        1: {
            "description": "Published research that identifies the basic principles that underlie a technology.\nScientific research begins to be translated into more applied research and development."
        },
        2: {
            "description": "The potential technology/product concept is defined and described.\nPractical applications can be defined/researched but are speculative and no proof or detailed analysis."
        },
        3: {
            "description": "Active R&D is initiated to develop the technology/product further.\nAnalytical studies and laboratory-based or experimental studies are performed to physically validate that analytical predictions are correct."
        },
        4: {
            "description": "Basic technological components are integrated to establish that they will work together.\nThis is relatively \u201Clow fidelity\u201D compared with the eventual system."
        },
        5: {
            "description": "Basic technological components integrated with reasonably realistic supporting elements so they can be tested in a simulated environment.\nFidelity of breadboard technology increases significantly."
        },
        6: {
            "description": "Representative model or prototype system, tested in a relevant environment.\nRepresents a major step up and requires evidence of performance on full-scale, realistic problems."
        },
        7: {
            "description": "Prototype near or at planned operational system.\nRequiring demonstration of an actual system prototype in an operational environment.\nCritical technological properties are measured against requirements."
        },
        8: {
            "description": "Technology has been proven to work in its final form and under expected conditions.\nIn almost all cases, this TRL represents the end of true system development."
        },
        9: {
            "description": "Actual application of the technology in its final form and under mission/operational conditions.\nTechnology is ready for commercial deployment."
        }
    },
    "CRL": {
        1: {
            "description": "Thinking that a possible need/problem or opportunity might exist in a market.\nNo clear hypotheses on who customers are and what problems are.\nLimited or non-existing knowledge of the market and customers/users."
        },
        2: {
            "description": "Some market research is performed, typically derived from secondary sources.\nBrief familiarity with the market, possible customers and their problems/needs.\nProduct/solution ideas may exist, but are not clear and typically speculative."
        },
        3: {
            "description": "Initiated customer discovery with feedback from primary market research.\nA more developed understanding of possible customers and possible customer segments.\nA more clear problem hypothesis."
        },
        4: {
            "description": "Contacts and feedback are established with several possible customers/users.\nThe problem and need (and its importance) is confirmed from multiple customers/users.\nCustomer segmentation in place, a primary product hypothesis is defined."
        },
        5: {
            "description": "General interest from customers/users for the product where the possible product/solution is confirmed to solve customers' problems.\nEstablished relationships with potential target customers, users or partners.\nDefined who the target customers/segments are to be focused on."
        },
        6: {
            "description": "Testing of product by customers/users where the value and benefits of the product is confirmed.\nPartnerships formed with key stakeholders in value chain.\nInitiated structured business development/sales activities."
        },
        7: {
            "description": "Customer agreements in place \u2013 first sales and/or test sales of product versions take place.\nCustomers and relevant stakeholders engaged in product qualifications/extended testing.\nRamp up of business development and sales efforts."
        },
        8: {
            "description": "Customer qualifications are complete and initial products are sold to a few customers.\nPayment willingness confirmed from sufficient % of customers (product-market fit validated).\nThe real buyers/economic decision makers are identified."
        },
        9: {
            "description": "Widespread product deployment, sales to several customers in a repeatable and scalable way.\nCustomer creation \u2013 company focuses on execution with growth of sales and efforts to build user/customer demand."
        }
    },
    "BRL": {
        1: {
            "description": "Vague and unspecific description of the potential business idea or business concept.\nLittle insight into the market and its potential/size.\nLittle knowledge or insight into competition and alternative solutions."
        },
        2: {
            "description": "Described the proposed business concept in some structured form.\nOne or several markets or applications are identified and described on overall level.\nSome competitors and/or alternatives are identified and listed."
        },
        3: {
            "description": "Draft of the business model in a canvas format (business model canvas/lean canvas) but typically without the revenues/cost parts.\nThe market potential and the market size is quantified with TAM and SAM.\nA more complete competitor overview with direct/indirect competitors."
        },
        4: {
            "description": "There is a full business model in canvas format incl. details on possible revenues/costs.\nFirst economic projections with numbers to show the market potential and economic viability.\nMade a competitive analysis on your position and uniqueness/differentiation."
        },
        5: {
            "description": "The business model (at least parts of it) is tested against customers for verifying hypotheses.\nThere is a first version of a more detailed revenue model incl. pricing hypotheses.\nThe competitive position and differentiation is verified by market feedback."
        },
        6: {
            "description": "A complete business model incl. the pricing is tested vs. customers by test sales or similar.\nThe revenue model incl. pricing is updated and refined based on customer feedback.\nFirst more complete projections on revenue/costs."
        },
        7: {
            "description": "There is product/market fit meaning you can demonstrate significant customer interest and sales where customers show clear payment willingness.\nAttractive revenue vs cost projections being validated by sales and data.\nPreparations for scaling business with suppliers, sales channels."
        },
        8: {
            "description": "Sales and other metrics show the business model holds and is profitable.\nThe business model shows it can scale (potentially globally). Sales channels and supply chain are fully in place.\nBusiness model is set but is continuously fine-tuned to explore more revenue options."
        },
        9: {
            "description": "Business model is final and business is scaling with growing and recurring revenues.\nThe business scales by growing in new markets, new geographies, new segments.\nThere is a working business which is profitable and sustainable over time."
        }
    },
    "FRL": {
        1: {
            "description": "Initial business idea with unclear/poor description \u2013 no value proposition.\nNo insight into how much funding needed and for what.\nLittle insight into different funding options and funding types."
        },
        2: {
            "description": "The business idea/business concept is reasonably well described incl. first version of value proposition.\nThe initial funding needs are mapped for initial key steps and milestones.\nThere is a basic plan with funding options for initial milestones (3-6 months)."
        },
        3: {
            "description": "Well described business concept and initial verification plan (incl. hypothesis to verify, goals).\nBasic insight and knowledge of different financing options.\nObtained first small soft funding for commercial verification."
        },
        4: {
            "description": "A succinct pitch (oral) and good written presentation of business concept is in place.\nThere is a more complete plan for funding needs/options over time (12-18 months).\nOverall budget and potential sources of funding."
        },
        5: {
            "description": "There is an investor presentation (pitch deck) that has been tested and is being fine-tuned.\nSupporting material e.g. financial projections and budgets etc. are being developed.\nApplications for other types of funding e.g. grants or loans are prepared and filed."
        },
        6: {
            "description": "There is an investor pitch deck that has been tested and fine-tuned which includes a focus on the business potential and financials.\nInsight into equity financing especially how investors think/evaluate.\nDecided to pursue equity funding and take in new owners."
        },
        7: {
            "description": "There is a team that can present well the investment case where key areas are in place such as prototype, traction/customer interest, market potential.\nThere is a complete business plan with financials and milestone plan.\nDiscussions with potential investors are on-going around a defined offer."
        },
        8: {
            "description": "The company is reasonably structured e.g. in terms of agreements, ownership etc.\nThere is formal order in the company e.g. bookkeeping, documentation.\nClear interest and discussions on term sheet level with interested investor(s).\nAll necessary material often required by investors in place."
        },
        9: {
            "description": "Investment formally concluded with all relevant documentation and money obtained.\nAdditional future investment needs and options are continuously being considered for future."
        }
    }
}

for rl_name, levels in RL_DATA.items():
    template, created = RLTemplate.objects.get_or_create(name=rl_name)
    for lvl_num, data in levels.items():
        RLTemplateLevel.objects.get_or_create(
            template=template,
            level=lvl_num,
            defaults={'description': data['description']}
        )

print("RL Template data populated successfully!")
