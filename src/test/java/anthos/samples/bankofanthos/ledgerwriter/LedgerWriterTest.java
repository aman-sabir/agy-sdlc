package anthos.samples.bankofanthos.ledgerwriter;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import java.math.BigDecimal;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
public class LedgerWriterTest {

    @LocalServerPort
    private int port;

    @Autowired
    private TestRestTemplate restTemplate;

    @org.springframework.boot.test.mock.mockito.MockBean
    private org.springframework.web.client.RestTemplate restTemplateBean;

    @org.junit.jupiter.api.BeforeEach
    public void setUp() {
        org.mockito.Mockito.when(restTemplateBean.exchange(
                org.mockito.ArgumentMatchers.anyString(),
                org.mockito.ArgumentMatchers.any(org.springframework.http.HttpMethod.class),
                org.mockito.ArgumentMatchers.any(org.springframework.http.HttpEntity.class),
                org.mockito.ArgumentMatchers.any(Class.class)))
            .thenReturn(new ResponseEntity<>(100000000, HttpStatus.OK));
    }

    @Test
    public void testStandardTransactionSuccess() {
        Transaction tx = new Transaction(null, "1234567890", "0987654321", new BigDecimal("500.00"));
        
        ResponseEntity<Transaction> response = restTemplate.postForEntity(
                "http://localhost:" + port + "/transactions", tx, Transaction.class);

        assertEquals(HttpStatus.CREATED, response.getStatusCode());
        assertNotNull(response.getBody().getTransactionId());
        assertFalse(response.getBody().getFlaggedForAml());
        assertEquals("PROCESSED", response.getBody().getStatus());
    }
}
