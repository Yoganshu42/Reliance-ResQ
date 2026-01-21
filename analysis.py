
def run_dashboard(selection=None):
    import streamlit as st
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter

    st.set_page_config(layout="wide")
    # st.title("📊 Reliance ResQ – Sales, Claims & Loss Ratio Dashboard (2025)")
    # st.info("This dashboard updates automatically when underlying data changes.")

    df_sales = pd.read_excel(
        r'C:\Users\yogan\OneDrive\Desktop\reliance\Reliance ResQ Sales data & Claim Data.xlsx',
        sheet_name=0
    )
    df_claims = pd.read_excel(
        r'C:\Users\yogan\OneDrive\Desktop\reliance\Reliance ResQ Sales data & Claim Data.xlsx',
        sheet_name=1
    )

    df_sales['Brand'] = df_sales['Brand'].replace({
        'Idea': 'Lenovo',
        'Pad': 'Redmi',
        'GooglePixel': 'Google'
    })


    df_sales = df_sales.drop([
        'Transaction Total','Transaction Date','Week','Plan ID','Mobile No','City',
        'Pincode','Product Description','Duration','Duration.1',
        'Manufacturer Warranty','Plan Tenure','Serial No./IMEI'
    ], axis=1)

    df_claims_25 = df_claims[df_claims['Day of Call_Date'].dt.year == 2025].copy()

    df_claims_25['Warranty Type'] = df_claims_25['Warranty Type'].replace({
        'Screen Protection': 'Cracked Screen'
    })

    df_claims_25['Product Brand(Group)'] = (
        df_claims_25['Product Brand(Group)'].replace({'OPPO': 'Oppo'})
    )

    df_claims_25['One time deductible'] = df_claims_25['One time deductible'].fillna(999)

    df_sales = df_sales.rename(columns={'Zopper Share': 'Plan Selling Price'})
    df_sales['Plan Start Date'] = pd.to_datetime(df_sales['Plan Start Date'], errors='coerce')
    df_sales['Plan End Date'] = pd.to_datetime(df_sales['Plan End Date'], errors='coerce')

    df_sales_25 = df_sales[df_sales['Plan Start Date'].dt.year == 2025].copy()

    df_sales_25['Coverage Days'] = (
        df_sales_25['Plan End Date'] - df_sales_25['Plan Start Date']
    ).dt.days.clip(lower=1)

    valuation_date = pd.to_datetime("2025-12-31")

    df_sales_25['Exposure Days'] = (
        valuation_date - df_sales_25['Plan Start Date']
    ).dt.days

    df_sales_25['Written Premium'] = df_sales_25['Zopper Shared ( Transfer Price )'] * 1.18

    df_sales_25['Zopper Earned Premium'] = (
        df_sales_25['Written Premium'] *
        (df_sales_25['Exposure Days'] / df_sales_25['Coverage Days'])
    )

    df_sales_25['Gross Premium'] = df_sales_25['Plan Selling Price']

    df_sales_25['Earned Premium'] = (
        df_sales_25['Gross Premium'] *
        (df_sales_25['Exposure Days'] / df_sales_25['Coverage Days'])
    )
    if selection in (None, "plan"):
        st.header("💰 Gross Premium by Plan Type")

        brand_ep = (
            df_sales_25
            .groupby('Plan Type')['Gross Premium']
            .sum()
            .sort_values(ascending=False)
        )

        fig, ax = plt.subplots(figsize=(12, 4))
        bars = ax.bar(brand_ep.index, brand_ep.values)
        ax.set_title('Gross Premium by Plan Type - 2025')
        ax.set_ylabel('Premium (INR)')
        ax.set_xticklabels(brand_ep.index, rotation=45, ha='right')
        ax.grid(axis='y', linestyle='--', alpha=0.6)

        for bar in bars:
            h = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width()/2,
                h,
                f'{h/1e7:.2f} Cr',
                ha='center',
                va='bottom',
                fontsize=9
            )

        st.pyplot(fig)

        st.header("📦 Plans Sold vs Claims Count with Loss Ratio – Plan Type")

        plans_by_plan = df_sales_25.groupby('Plan Type').size()
        claims_by_plan = df_claims_25.groupby('Warranty Type').size()

        zopper_earned_by_plan = df_sales_25.groupby('Plan Type')['Zopper Earned Premium'].sum()
        zopper_claim_by_plan = df_claims_25.groupby('Warranty Type')["Zopper's Cost"].sum()
        deductible_by_plan = df_claims_25.groupby('Warranty Type')['One time deductible'].sum()

        plan_data = pd.concat(
            [
                plans_by_plan,
                claims_by_plan,
                zopper_earned_by_plan,
                zopper_claim_by_plan,
                deductible_by_plan
            ],
            axis=1
        ).fillna(0)

        plan_data.columns = [
            'Plans Sold',
            'Claims Count',
            'Zopper Earned Premium',
            "Zopper's Cost",
            'One time deductible'
        ]

        plan_data['Net Claims'] = (
            plan_data["Zopper's Cost"] - plan_data['One time deductible']
        )

        plan_data['Loss Ratio (%)'] = (
            plan_data['Net Claims'] / plan_data['Zopper Earned Premium'] * 100
        ).replace([np.inf, -np.inf], 0).fillna(0)

        plan_data = plan_data.sort_values('Plans Sold', ascending=False)

        x = np.arange(len(plan_data))
        width = 0.35

        fig, ax1 = plt.subplots(figsize=(20, 10))

        b0 = ax1.bar(x - width/2, plan_data['Plans Sold'], width, label='Plans Sold')
        b1 = ax1.bar(x + width/2, plan_data['Claims Count'], width, label='Claims Count')

        ax1.set_title('Plan Type-wise Plans Sold vs Claims Count with Loss Ratio – 2025')
        ax1.set_xlabel('Plan Type')
        ax1.set_ylabel('Count')
        ax1.set_xticks(x)
        ax1.set_xticklabels(plan_data.index, rotation=45, ha='right')
        ax1.grid(axis='y', linestyle='--', alpha=0.4)

        ax2 = ax1.twinx()

        ax2.plot(
            x,
            plan_data['Loss Ratio (%)'],
            color='black',
            marker='o',
            linewidth=2,
            alpha=0.6,
            label='Loss Ratio (%)'
        )

        ax2.set_ylabel('Loss Ratio (%)')
        ax2.set_ylim(0, plan_data['Loss Ratio (%)'].max() * 1.3)

        for bars in [b0, b1]:
            for bar in bars:
                h = bar.get_height()
                if h > 0:
                    ax1.text(
                        bar.get_x() + bar.get_width()/2,
                        h,
                        f'{int(h)}',
                        ha='center',
                        va='bottom',
                        fontsize=9
                    )

        for i, val in enumerate(plan_data['Loss Ratio (%)']):
            if val > 0:
                ax2.annotate(
                    f'{val:.1f}%',
                    xy=(x[i], val),
                    xytext=(0, 8),
                    textcoords='offset points',
                    ha='center',
                    fontsize=10,
                    fontweight='bold'
                )

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()

        ax1.legend(
            lines1 + lines2,
            labels1 + labels2,
            loc='upper right',
            fontsize=11
        )

        st.pyplot(fig)

        import streamlit as st
        import numpy as np
        import pandas as pd
        import matplotlib.pyplot as plt

        st.subheader("📊 Plan-wise Premium, Claims & Loss Ratio – 2025")

        gross_premium_by_brand = (
            df_sales_25
            .groupby('Plan Type')['Gross Premium']
            .sum()
        )

        earned_premium_by_brand = (
            df_sales_25
            .groupby('Plan Type')['Earned Premium']
            .sum()
        )

        zopper_earned_by_brand = (
            df_sales_25
            .groupby('Plan Type')['Zopper Earned Premium']
            .sum()
        )

        df_claims_25['Net Claim Cost'] = (
            df_claims_25["Zopper's Cost"] - df_claims_25['One time deductible']
        )

        net_claim_by_brand = (
            df_claims_25
            .groupby('Warranty Type')['Net Claim Cost']
            .sum()
        )

        deductible_by_brand = (
            df_claims_25
            .groupby('Warranty Type')['One time deductible']
            .sum()
        )

        brand_data = (
            pd.concat(
                [
                    gross_premium_by_brand,
                    earned_premium_by_brand,
                    zopper_earned_by_brand,
                    net_claim_by_brand,
                    deductible_by_brand
                ],
                axis=1
            )
            .fillna(0)
        )

        brand_data.columns = [
            'Gross Premium',
            'Earned Premium',
            'Zopper Earned Premium',
            'Net Claims',
            'One time deductible'
        ]

        brand_data = brand_data.sort_values('Earned Premium', ascending=False)

        brand_data['Loss Ratio (%)'] = (
            brand_data['Net Claims'] /
            brand_data['Zopper Earned Premium'] * 100
        ).replace([np.inf, -np.inf], 0).fillna(0)

        x = np.arange(len(brand_data))
        width = 0.15

        fig, ax = plt.subplots(figsize=(20, 10))

        b0 = ax.bar(x - 2*width, brand_data['Gross Premium'], width, label='Gross Premium')
        b1 = ax.bar(x - width,   brand_data['Earned Premium'], width, label='Earned Premium')
        b2 = ax.bar(x,           brand_data['Zopper Earned Premium'], width, label='Zopper Earned Premium')
        b3 = ax.bar(x + width,   brand_data['Net Claims'], width, label='Net Claims')
        b4 = ax.bar(x + 2*width, brand_data['One time deductible'], width, label='One Time Deductible')

        ax.set_title('Plan-wise Premium, Claims & Loss Ratio – 2025')
        ax.set_ylabel('Amount (INR)')
        ax.set_xticks(x)
        ax.set_xticklabels(brand_data.index, rotation=45, ha='right')
        ax.grid(axis='y', linestyle='--', alpha=0.6)

        ax2 = ax.twinx()
        ax2.plot(
            x,
            brand_data['Loss Ratio (%)'],
            marker='o',
            linewidth=1.5,
            alpha=0.6,
            label='Loss Ratio (%)'
        )
        ax2.set_ylabel('Loss Ratio (%)')
        ax2.set_ylim(0, brand_data['Loss Ratio (%)'].max() * 1.1)

        for i, v in enumerate(brand_data['Loss Ratio (%)']):
            ax2.text(
                x[i],
                v,
                f'{v:.1f}%',
                ha='left',
                va='bottom',
                fontsize=12
            )

        for bars in [b0, b1, b2, b3, b4]:
            for bar in bars:
                h = bar.get_height()
                if h > 0:
                    ax.text(
                        bar.get_x() + bar.get_width()/2,
                        h,
                        f'{h/1e7:.2f} Cr',
                        ha='center',
                        va='bottom',
                        fontsize=10
                    )

        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='upper right')

        st.pyplot(fig)

        plans_by_plan = df_sales_25.groupby('Plan Type').size()
        claims_by_plan = df_claims_25.groupby('Warranty Type').size()

        zopper_earned_by_plan = (
            df_sales_25
            .groupby('Plan Type')['Zopper Earned Premium']
            .sum()
        )

        zopper_claim_by_plan = (
            df_claims_25
            .groupby('Warranty Type')["Zopper's Cost"]
            .sum()
        )

        deductible_by_plan = (
            df_claims_25
            .groupby('Warranty Type')['One time deductible']
            .sum()
        )

        plan_data = (
            pd.concat(
                [
                    plans_by_plan,
                    claims_by_plan,
                    zopper_earned_by_plan,
                    zopper_claim_by_plan,
                    deductible_by_plan
                ],
                axis=1
            )
            .fillna(0)
        )

        plan_data.columns = [
            'Plans Sold',
            'Claims Count',
            'Zopper Earned Premium',
            "Zopper's Cost",
            'One time deductible'
        ]

        plan_data['Net Claims'] = (
            plan_data["Zopper's Cost"] - plan_data['One time deductible']
        )

        plan_data['Loss Ratio (%)'] = (
            plan_data['Net Claims'] / plan_data['Zopper Earned Premium'] * 100
        ).replace([np.inf, -np.inf], 0).fillna(0)

        plan_data = plan_data.sort_values('Plans Sold', ascending=False)

        x = np.arange(len(plan_data))
        width = 0.35

        fig, ax1 = plt.subplots(figsize=(20, 10))

        b0 = ax1.bar(
            x - width/2,
            plan_data['Plans Sold'],
            width,
            label='Plans Sold'
        )

        b1 = ax1.bar(
            x + width/2,
            plan_data['Claims Count'],
            width,
            label='Claims Count'
        )

        ax1.set_title(
            'Plan Type-wise Plans Sold vs Claims Count with Loss Ratio – 2025',
            fontsize=16,
            fontweight='bold'
        )

        ax1.set_xlabel('Plan Type')
        ax1.set_ylabel('Count')
        ax1.set_xticks(x)
        ax1.set_xticklabels(plan_data.index, rotation=45, ha='right')
        ax1.grid(axis='y', linestyle='--', alpha=0.4)

        ax2 = ax1.twinx()

        ax2.plot(
            x,
            plan_data['Loss Ratio (%)'],
            color='black',
            marker='o',
            linewidth=2,
            alpha=0.6,
            label='Loss Ratio (%)'
        )

        ax2.set_ylabel('Loss Ratio (%)')
        ax2.set_ylim(0, plan_data['Loss Ratio (%)'].max() * 1.3)

        for bars in [b0, b1]:
            for bar in bars:
                h = bar.get_height()
                if h > 0:
                    ax1.text(
                        bar.get_x() + bar.get_width()/2,
                        h,
                        f'{int(h)}',
                        ha='center',
                        va='bottom',
                        fontsize=9
                    )

        for i, val in enumerate(plan_data['Loss Ratio (%)']):
            if val > 0:
                ax2.annotate(
                    f'{val:.1f}%',
                    xy=(x[i], val),
                    xytext=(0, 8),
                    textcoords='offset points',
                    ha='center',
                    fontsize=10,
                    fontweight='bold'
                )

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()

        ax1.legend(
            lines1 + lines2,
            labels1 + labels2,
            loc='upper right',
            fontsize=11
        )

        plt.tight_layout()
        st.pyplot(fig)


    # from matplotlib.ticker import FuncFormatter
    if selection in (None, "brand"):
    # PLAN-WISE PLOTS ONLY

        gross_by_brand = df_sales_25.groupby('Brand')['Gross Premium'].sum()
        earned_by_brand = df_sales_25.groupby('Brand')['Earned Premium'].sum()
        zopper_earned_by_brand = df_sales_25.groupby('Brand')['Zopper Earned Premium'].sum()

        zopper_claim_by_brand = (
            df_claims_25
            .groupby('Product Brand(Group)')["Zopper's Cost"]
            .sum()
        )

        deductible_by_brand = (
            df_claims_25
            .groupby('Product Brand(Group)')['One time deductible']
            .sum()
        )

        brand_data = (
            pd.concat(
                [
                    gross_by_brand,
                    earned_by_brand,
                    zopper_earned_by_brand,
                    zopper_claim_by_brand,
                    deductible_by_brand
                ],
                axis=1
            )
            .fillna(0)
        )

        brand_data.columns = [
            'Gross Premium',
            'Earned Premium',
            'Zopper Earned Premium',
            "Zopper's Cost",
            'One time deductible'
        ]

        brand_data = brand_data.sort_values('Gross Premium', ascending=False)

        brand_data['Net Claims'] = (
            brand_data["Zopper's Cost"] - brand_data['One time deductible']
        )

        brand_data['Loss Ratio (%)'] = (
            brand_data['Net Claims'] / brand_data['Zopper Earned Premium'] * 100
        ).replace([np.inf, -np.inf], 0).fillna(0)

        fig, ax1 = plt.subplots(figsize=(20, 12))
        x = np.arange(len(brand_data))

        w_gross = 0.85
        w_earned = 0.55
        w_zopper_earned = 0.45
        w_claims = 0.25
        w_deduct = 0.10  

        bar_gross = ax1.bar(
            x,
            brand_data['Gross Premium'],
            width=w_gross,
            label='Gross Premium',
            color='#E3F2FD',
            edgecolor='#90CAF9',
            linewidth=1
        )

        bar_earned = ax1.bar(
            x,
            brand_data['Earned Premium'],
            width=w_earned,
            label='Earned Premium',
            color="#93C8F3"
        )

        bar_z_earned = ax1.bar(
            x,
            brand_data['Zopper Earned Premium'],
            width=w_zopper_earned,
            label='Zopper Earned Premium',
            color="#A8F393"
        )

        bar_claims = ax1.bar(
            x,
            brand_data["Zopper's Cost"],
            width=w_claims,
            label="Zopper Claim Cost",
            color="#C58BE5"
        )

        bar_deduct = ax1.bar(
            x,
            brand_data['One time deductible'],
            width=w_deduct,
            label='One Time Deductible',
            color="#FFFB00"
        )

        ax1.set_yscale('log')

        def human_readable_lakhs(x, pos):
            if x >= 1e5:
                return f'{x/1e5:.0f}L'
            elif x >= 1e3:
                return f'{x/1e3:.0f}k'
            return str(int(x))

        ax1.yaxis.set_major_formatter(FuncFormatter(human_readable_lakhs))

        ax1.set_title(
            'Brand-wise Financials: Revenue, Claims & Deductibles (Log Scale)',
            fontsize=16,
            pad=20,
            fontweight='bold'
        )

        ax1.set_xlabel('Brand', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Amount (INR) - Logarithmic Scale', fontsize=12)
        ax1.set_xticks(x)
        ax1.set_xticklabels(brand_data.index, rotation=45, ha='right', fontsize=11)

        ax1.grid(axis='y', which='major', linestyle='-', alpha=0.3, color='gray')
        ax1.grid(axis='y', which='minor', linestyle=':', alpha=0.1, color='gray')

        ax2 = ax1.twinx()

        ax2.plot(
            x,
            brand_data['Loss Ratio (%)'],
            color='black',
            marker='o',
            linewidth=2,
            markersize=8,
            alpha=0.6,
            label='Loss Ratio (%)'
        )

        ax2.set_ylabel('Loss Ratio (%)', fontsize=12)
        ax2.set_ylim(0, brand_data['Loss Ratio (%)'].max() * 1.3)

        def add_labels(bars, ax, color, y_offset_factor, font_size):
            for bar in bars:
                h = bar.get_height()
                if h <= 0:
                    continue
                label = f'{h/1e5:.1f}L' if h >= 1e5 else f'{h/1e5:.2f}L'
                ax.text(
                    bar.get_x() + bar.get_width()/2,
                    h * y_offset_factor,
                    label,
                    ha='center',
                    va='bottom',
                    fontsize=font_size,
                    fontweight='bold',
                    color=color
                )

        add_labels(bar_gross, ax1, '#1565C0', 1.02, 10)
        add_labels(bar_earned, ax1, 'white', 0.6, 9)
        add_labels(bar_z_earned, ax1, '#2E7D32', 0.6, 9)
        add_labels(bar_claims, ax1, '#6A1B9A', 1.1, 9)
        add_labels(bar_deduct, ax1, "#000000", 1.4, 8)

        for i, val in enumerate(brand_data['Loss Ratio (%)']):
            if val > 0:
                ax2.annotate(
                    f'{val:.1f}%',
                    xy=(x[i], val),
                    xytext=(2, 10),
                    textcoords='offset points',
                    ha='center',
                    fontsize=10,
                    fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", alpha=0.8)
                )

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()

        ax1.legend(
            lines1 + lines2,
            labels1 + labels2,
            loc='upper right',
            fontsize=11,
            frameon=True,
            shadow=True
        )

        plt.tight_layout()
        st.pyplot(fig)

        plans_by_brand = df_sales_25.groupby('Brand').size()
        claims_by_brand = df_claims_25.groupby('Product Brand(Group)').size()

        zopper_earned_by_brand = (
            df_sales_25
            .groupby('Brand')['Zopper Earned Premium']
            .sum()
        )

        zopper_claim_by_brand = (
            df_claims_25
            .groupby('Product Brand(Group)')["Zopper's Cost"]
            .sum()
        )

        deductible_by_brand = (
            df_claims_25
            .groupby('Product Brand(Group)')['One time deductible']
            .sum()
        )

        brand_data = (
            pd.concat(
                [
                    plans_by_brand,
                    claims_by_brand,
                    zopper_earned_by_brand,
                    zopper_claim_by_brand,
                    deductible_by_brand
                ],
                axis=1
            )
            .fillna(0)
        )

        brand_data.columns = [
            'Plans Sold',
            'Claims Count',
            'Zopper Earned Premium',
            "Zopper's Cost",
            'One time deductible'
        ]

        brand_data['Net Claims'] = (
            brand_data["Zopper's Cost"] - brand_data['One time deductible']
        )

        brand_data['Loss Ratio (%)'] = (
            brand_data['Net Claims'] / brand_data['Zopper Earned Premium'] * 100
        ).replace([np.inf, -np.inf], 0).fillna(0)

        brand_data = brand_data.sort_values('Plans Sold', ascending=False)

        x = np.arange(len(brand_data))
        width = 0.35

        fig, ax1 = plt.subplots(figsize=(20, 10))

        b0 = ax1.bar(
            x - width/2,
            brand_data['Plans Sold'],
            width,
            label='Plans Sold'
        )

        b1 = ax1.bar(
            x + width/2,
            brand_data['Claims Count'],
            width,
            label='Claims Count'
        )

        ax1.set_title(
            'Brand-wise Plans Sold vs Claims Count with Loss Ratio',
            fontsize=16,
            fontweight='bold'
        )

        ax1.set_xlabel('Brand')
        ax1.set_ylabel('Count')
        ax1.set_xticks(x)
        ax1.set_xticklabels(brand_data.index, rotation=45, ha='right')
        ax1.grid(axis='y', linestyle='--', alpha=0.4)

        ax2 = ax1.twinx()

        ax2.plot(
            x,
            brand_data['Loss Ratio (%)'],
            color='black',
            marker='o',
            linewidth=2,
            alpha=0.6,
            label='Loss Ratio (%)'
        )

        ax2.set_ylabel('Loss Ratio (%)')
        ax2.set_ylim(0, brand_data['Loss Ratio (%)'].max() * 1.3)

        for bars in [b0, b1]:
            for bar in bars:
                h = bar.get_height()
                if h > 0:
                    ax1.text(
                        bar.get_x() + bar.get_width()/2,
                        h,
                        f'{int(h)}',
                        ha='center',
                        va='bottom',
                        fontsize=9
                    )

        for i, val in enumerate(brand_data['Loss Ratio (%)']):
            if val > 0:
                ax2.annotate(
                    f'{val:.1f}%',
                    xy=(x[i], val),
                    xytext=(0, 8),
                    textcoords='offset points',
                    ha='center',
                    fontsize=10,
                    fontweight='bold'
                )

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()

        ax1.legend(
            lines1 + lines2,
            labels1 + labels2,
            loc='upper right',
            fontsize=11
        )

        plt.tight_layout()
        st.pyplot(fig)

    if selection in (None, "state"):

        gross_premium_by_brand = (
            df_sales_25
            .groupby('State')['Gross Premium']
            .sum()
        )

        earned_premium_by_brand = (
            df_sales_25
            .groupby('State')['Earned Premium']
            .sum()
        )

        zopper_earned_by_brand = (
            df_sales_25
            .groupby('State')['Zopper Earned Premium']
            .sum()
        )

        brand_data = (
            pd.concat(
                [
                    gross_premium_by_brand,
                    earned_premium_by_brand,
                    zopper_earned_by_brand
                ],
                axis=1
            )
            .fillna(0)
        )

        brand_data.columns = [
            'Gross Premium',
            'Earned Premium',
            'Zopper Earned Premium'
        ]

        brand_data = brand_data.sort_values('Earned Premium', ascending=False)

        top5 = brand_data.head(5)
        bottom5 = brand_data.tail(5)

        def plot_nested_bar(data, title):
            x = np.arange(len(data))

            fig, ax = plt.subplots(figsize=(14, 6))

            b0 = ax.bar(x, data['Gross Premium'], width=0.6, label='Gross Premium')
            b1 = ax.bar(x, data['Earned Premium'], width=0.4, label='Earned Premium')
            b2 = ax.bar(x, data['Zopper Earned Premium'], width=0.25, label='Zopper Earned Premium')

            ax.set_title(title)
            ax.set_ylabel('Amount (INR)')
            ax.set_xticks(x)
            ax.set_xticklabels(data.index, rotation=45, ha='right')
            ax.grid(axis='y', linestyle='--', alpha=0.6)
            ax.legend()

            for bars in [b0, b1, b2]:
                for bar in bars:
                    h = bar.get_height()
                    if h > 0:
                        ax.text(
                            bar.get_x() + bar.get_width() / 2,
                            h,
                            f'{h / 1e5:.2f} L',
                            ha='center',
                            va='bottom',
                            fontsize=8
                        )

            plt.tight_layout()
            st.pyplot(fig)

        plot_nested_bar(
            top5,
            'Top 5 States: Gross vs Earned vs Zopper Earned Premium – 2025'
        )

        plot_nested_bar(
            bottom5,
            'Bottom 5 States: Gross vs Earned vs Zopper Earned Premium – 2025'
        )

    if selection in (None, 'period'):

        df_claims_period = df_claims.copy()

        df_claims_period['purchase_to_claim_days'] = (
            pd.to_datetime(df_claims_period['Day of Call_Date']) -
            pd.to_datetime(df_claims_period['Day of Product Purchased Date 2'])
        ).dt.days

        bins = [-1, 7, 30, 90, 10_000]
        labels = ['0-7 days', '8-30 days', '31-90 days', '90+ days']

        df_claims_period['purchase_claim_bucket'] = pd.cut(
            df_claims_period['purchase_to_claim_days'],
            bins=bins,
            labels=labels
        )

        brand_bucket_pivot = (
            df_claims_period
            .groupby(['Product Brand(Group)', 'purchase_claim_bucket'])
            .size()
            .unstack(fill_value=0)
            .reset_index()
        )

        for brand, data in brand_bucket_pivot.groupby('Product Brand(Group)'):
            values = data[labels].iloc[0]

            fig, ax = plt.subplots(figsize=(12, 4))
            bars = ax.bar(labels, values)

            ax.set_xlabel('Return Period')
            ax.set_ylabel('Number of Claims')
            ax.set_title(f'Claim Return Period – {brand}')

            for bar in bars:
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    height,
                    int(height),
                    ha='center',
                    va='bottom'
                )

            plt.tight_layout()
            st.pyplot(fig)

    if selection in (None, "prediction"):

        st.subheader("📈 Sales & Claims Prediction Analysis")

        # ---------------- CLAIMS ---------------- #

        df_claims_25['call_date'] = pd.to_datetime(df_claims['Day of Call_Date'])

        monthly_claims = (
            df_claims_25
            .set_index('call_date')
            .resample('M')
            .size()
            .rename('claims')
        )

        monthly_claims_aug_dec = monthly_claims[
            monthly_claims.index.month.isin([8, 9, 10, 11, 12])
        ]

        claims = monthly_claims_aug_dec.values[-3:]
        weights = np.array([0.2, 0.3, 0.5])

        jan_2026_pred_wma = int(np.dot(claims, weights))

        y = monthly_claims_aug_dec.values
        x = np.arange(len(y))

        coef = np.polyfit(x, y, 1)
        jan_2026_pred_trend = int(np.polyval(coef, len(y)))

        jan_2026_pred_avg = int(y.mean())

        recent = monthly_claims_aug_dec.values[-3:]
        drift = (monthly_claims_aug_dec.values[-1] - monthly_claims_aug_dec.values[-3]) / 2
        jan_2026_pred = int(recent.mean() + 0.5 * drift)

        # ---------------- SALES ---------------- #

        df_sales_25 = df_sales_25.copy()
        df_sales_25['Plan Start Date'] = pd.to_datetime(
            df_sales_25['Plan Start Date'], errors='coerce'
        )

        month_order = ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        monthly_sales = (
            df_sales_25['Month']
            .value_counts()
            .reindex(month_order)
        )

        def damped_growth_prediction(series, cap=1.15):
            recent = series[-3:]
            growth = (recent[1:] / recent[:-1]).mean()
            damped_growth = min(growth, cap)
            return int(recent[-1] * damped_growth)

        sales_series = monthly_sales.values

        sales_pred_dec = damped_growth_prediction(sales_series[:-1])
        sales_actual_dec = sales_series[-1]

        sales_pred_jan = damped_growth_prediction(sales_series)

        claims_series = monthly_claims.values

        claims_pred_dec = damped_growth_prediction(claims_series[:-1])
        claims_actual_dec = claims_series[-1]

        claims_pred_jan = damped_growth_prediction(claims_series)

        # ---------------- DISPLAY RESULTS ---------------- #

        st.write("📦 **SALES PREDICTION**")
        st.write(f"Predicted DEC Sales (Jul–Nov): {sales_pred_dec}")
        st.write(f"Actual DEC Sales            : {sales_actual_dec}")
        st.write(f"Predicted JAN Sales (Jul–Dec): {sales_pred_jan}")

        st.write("📞 **CLAIMS PREDICTION**")
        st.write(f"Predicted DEC Claims (Aug–Nov): {claims_pred_dec}")
        st.write(f"Actual DEC Claims            : {claims_actual_dec}")
        st.write(f"Predicted JAN Claims (Aug–Dec): {jan_2026_pred}")

        # ---------------- SALES PLOT ---------------- #

        months_sales = ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan (Pred)']
        sales_values = [*monthly_sales.values, sales_pred_jan]

        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(months_sales[:-1], sales_values[:-1], marker='o', label='Actual Sales')
        ax.plot(months_sales[-2:], sales_values[-2:], linestyle='--', marker='o', label='Predicted Sales')

        ax.annotate(
            f"Jan: {sales_pred_jan}",
            xy=(len(months_sales)-1, sales_pred_jan),
            xytext=(len(months_sales)-1.3, sales_pred_jan + 300),
            arrowprops=dict(arrowstyle="->")
        )

        for i, val in enumerate(sales_values[:-1]):
            ax.text(i, val, str(val), ha='center', va='bottom')

        ax.set_title("📦 Monthly Sales with January Prediction")
        ax.set_ylabel("Plans Sold")
        ax.legend()
        plt.tight_layout()
        st.pyplot(fig)

        # ---------------- CLAIMS PLOT ---------------- #

        months_claims = ['Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan (Pred)']
        claims_values = [*monthly_claims.values, jan_2026_pred]

        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(months_claims[:-1], claims_values[:-1], marker='o', label='Actual Claims')
        ax.plot(months_claims[-2:], claims_values[-2:], linestyle='--', marker='o', label='Predicted Claims')

        ax.annotate(
            f"Jan: {jan_2026_pred}",
            xy=(len(months_claims)-1, jan_2026_pred),
            xytext=(len(months_claims)-1.3, jan_2026_pred + 4),
            arrowprops=dict(arrowstyle="->")
        )

        for i, val in enumerate(monthly_claims.values):
            ax.text(i, val, str(val), ha='center', va='bottom')

        ax.set_title("📞 Monthly Claims with January Prediction")
        ax.set_ylabel("Number of Claims")
        ax.legend()
        plt.tight_layout()
        st.pyplot(fig)

        # -------- SALES ACCURACY (DEC VALIDATION) -------- #

        sales_abs_error = abs(sales_pred_dec - sales_actual_dec)
        sales_pct_error = (sales_abs_error / sales_actual_dec) * 100
        sales_accuracy = 100 - sales_pct_error


        # -------- CLAIMS ACCURACY (DEC VALIDATION) -------- #

        claims_abs_error = abs(claims_pred_dec - claims_actual_dec)
        claims_pct_error = (claims_abs_error / claims_actual_dec) * 100
        claims_accuracy = 100 - claims_pct_error


        # -------- STREAMLIT DISPLAY -------- #

        st.subheader("📦 Sales Model Accuracy (DEC Validation)")
        st.write(f"**Predicted DEC Sales:** {sales_pred_dec}")
        st.write(f"**Actual DEC Sales:** {sales_actual_dec}")
        st.write(f"**Absolute Error:** {sales_abs_error}")
        st.write(f"**Percentage Error:** {sales_pct_error:.2f}%")
        st.success(f"**Model Accuracy:** {sales_accuracy:.2f}%")

        st.subheader("📞 Claims Model Accuracy (DEC Validation)")
        st.write(f"**Predicted DEC Claims:** {claims_pred_dec}")
        st.write(f"**Actual DEC Claims:** {claims_actual_dec}")
        st.write(f"**Absolute Error:** {claims_abs_error}")
        st.write(f"**Percentage Error:** {claims_pct_error:.2f}%")
        st.success(f"**Model Accuracy:** {claims_accuracy:.2f}%")


    st.success("✅ Dashboard rendered successfully. Update Excel file to see live changes.")
