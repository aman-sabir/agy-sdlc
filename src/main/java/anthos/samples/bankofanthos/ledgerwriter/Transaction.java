/*
 * Copyright 2020, Google LLC.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package anthos.samples.bankofanthos.ledgerwriter;

import java.math.BigDecimal;
import java.util.Date;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.Transient;

import org.hibernate.annotations.CreationTimestamp;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Defines a banking transaction.
 *
 * Timestamped at object creation time.
 */
@Entity
@Table(name = "TRANSACTIONS")
public final class Transaction {
    @Id
    @Column(name = "TRANSACTION_ID", nullable = false, updatable = false)
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private long transactionId;
    @Column(name = "FROM_ACCT", nullable = false, updatable = false)
    @JsonProperty("fromAccountNum")
    private String fromAccountNum;
    @Column(name = "FROM_ROUTE", nullable = false, updatable = false)
    @JsonProperty("fromRoutingNum")
    private String fromRoutingNum;
    @Column(name = "TO_ACCT", nullable = false, updatable = false)
    @JsonProperty("toAccountNum")
    private String toAccountNum;
    @Column(name = "TO_ROUTE", nullable = false, updatable = false)
    @JsonProperty("toRoutingNum")
    private String toRoutingNum;
    @Column(name = "AMOUNT", nullable = false, updatable = false)
    @JsonProperty("amount")
    private Integer amount;
    @Column(name = "TIMESTAMP", nullable = false, updatable = false)
    @CreationTimestamp
    @JsonProperty("timestamp")
    private Date timestamp;
    // UUID is used for preventing duplicate requests from client
    // Do not persist to database
    @Transient
    @JsonProperty("uuid")
    private String requestUuid = java.util.UUID.randomUUID().toString();

    @Column(name = "flagged_for_aml")
    @JsonProperty("flaggedForAml")
    private Boolean flaggedForAml = false;

    @Column(name = "regulatory_purpose_code")
    @JsonProperty("regulatoryPurposeCode")
    private String regulatoryPurposeCode;

    @Column(name = "status")
    @JsonProperty("status")
    private String status = "PROCESSED";

    private static final double CENTS_PER_DOLLAR = 100.0;

    public Transaction() {}

    public Transaction(Long transactionId, String fromAccountNum, String toAccountNum, BigDecimal amount) {
        this.transactionId = transactionId != null ? transactionId : 0L;
        this.fromAccountNum = fromAccountNum;
        this.toAccountNum = toAccountNum;
        this.amount = amount != null ? amount.multiply(BigDecimal.valueOf(100)).intValue() : 0;
        this.fromRoutingNum = "123456789";
        this.toRoutingNum = "123456789";
        this.status = "PROCESSED";
    }

    public Boolean getFlaggedForAml() {
        return flaggedForAml;
    }

    public void setFlaggedForAml(Boolean flaggedForAml) {
        this.flaggedForAml = flaggedForAml;
    }

    public String getRegulatoryPurposeCode() {
        return regulatoryPurposeCode;
    }

    public void setRegulatoryPurposeCode(String regulatoryPurposeCode) {
        this.regulatoryPurposeCode = regulatoryPurposeCode;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public long getTransactionId() {
        return transactionId;
    }

    public String getFromAccountNum() {
        return fromAccountNum;
    }

    public String getFromRoutingNum() {
        return fromRoutingNum;
    }

    public String getToAccountNum() {
        return toAccountNum;
    }

    public String getToRoutingNum() {
        return toRoutingNum;
    }

    public Integer getAmount() {
        return amount;
    }

    public String getRequestUuid() {
        if (requestUuid == null) {
            return "";
        } else {
            return requestUuid;
        }
    }

    /**
     * String representation.
     *
     * Formatting = "{accountNum}:{type}:{amount}"
     */
    public String toString() {
        return String.format("%s->$%.2f->%s",
                fromAccountNum, amount / CENTS_PER_DOLLAR, toAccountNum);
    }
}


